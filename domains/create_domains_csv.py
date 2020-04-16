import concurrent.futures
import csv
import io
from functools import partial
import logging
from multiprocessing import  Pool
import os
import re
import warnings

import numpy as np
import pandas as pd
import requests
import tldextract
from tqdm import tqdm

from agency_org_cleaner import rename_rows

logger = logging.getLogger(__name__)

warnings.filterwarnings("ignore")


def get_sites(tlds = ['gov', 'fed.us', 'mil']):
    sources = [
        'https://analytics.usa.gov/data/live/sites.csv',
        'https://analytics.usa.gov/data/live/second-level-domains.csv',
        'https://analytics.usa.gov/data/live/sites-extended.csv',
        'https://github.com/GSA/data/raw/master/end-of-term-archive-csv/eot-2016-seeds.csv',
        'https://github.com/GSA/data/raw/master/dotgov-websites/censys-federal-snapshot.csv',
        'https://github.com/GSA/data/raw/master/dotgov-websites/rdns-federal-snapshot.csv',
        'https://github.com/GSA/data/raw/master/dotgov-websites/other-websites.csv']
    
    sites = []
    
    for source in sources:
        try:
            r = requests.get(source)
        except Exception as e:
            logger.critical(f"{e} making request to {source}", exc_info=True)
            continue
        
        decoded_content = r.content.decode('utf-8')
        csv_reader = csv.reader(decoded_content.splitlines(), delimiter=',')
        
        for i, row in enumerate(csv_reader):            
            
            site = row[0].lower().strip()
            
            if "domain" in site:
                #this is a header
                continue
                
            parsed_site = tldextract.extract(site)
            
            domain = parsed_site.domain
            if not domain:
                # broken domains like fed.us, nsn.us, gov.pr, and #name?
                continue
            
            tld = parsed_site.suffix
            if tld not in tlds:
                continue
            
            subdomain = parsed_site.subdomain                    
            sites.append({'tld': tld,
                          'domain': domain,
                          'subdomain': subdomain,
                          'site':site})
    
    sites_df = pd.DataFrame(sites)
    sites_df = sites_df.astype(str)
    
    fed_df = pd.read_csv('https://github.com/GSA/data/raw/master/dotgov-domains/current-federal.csv')
    fed_df['Domain Name'] = fed_df['Domain Name'].apply(lambda x: x.lower().strip())
    parsed_domain_names = fed_df['Domain Name'].apply(lambda x: tldextract.extract(x))
    fed_df['tld'] = parsed_domain_names.apply(lambda x: x.suffix)
    fed_df['domain'] = parsed_domain_names.apply(lambda x: x.domain)
    fed_df['subdomain'] = parsed_domain_names.apply(lambda x: x.subdomain)
    
    fed_df = fed_df.astype(str)
    
    return sites_df, fed_df


def construct_url(row):
    tld = row['tld_fed']
    domain = row['domain']
    subdomain = row['subdomain_sites']
    
    if domain == subdomain or not subdomain:
        return f'{domain}.{tld}'
    else:
        return f'{subdomain}.{domain}.{tld}'


def schematize_url(constructed_url):
    if not re.search(r'^https?://', constructed_url):
        return f'https://{constructed_url}'
    else:
        return constructed_url


def try_head(schematized_url):
    try:
        #allow redirects since pa11y won't
        h = requests.head(schematized_url, timeout=(2, 5), allow_redirects=True)
    except requests.exceptions.Timeout:
        return 'timeout'
    except requests.exceptions.RequestException as e:
        return
    except Exception as e:
        print(e)
        return
    return h


def get_routeable_url(schematized_url):
    h = try_head(schematized_url)
    if not h:
        schematized_url = f'{schematized_url[:8]}www.{schematized_url[8:]}'
        h = try_head(schematized_url)
        if not h:
            schematized_url = schematized_url.replace('https','http')
            h = try_head(schematized_url)
            if not h:
                schematized_url = schematized_url.replace('www.','')
                h = try_head(schematized_url)
    if not h:
        return
    if h == 'timeout':
        return h
    if h.status_code == 200:
        return h.url


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("Downloading latest set of .gov domains from GSA's github")

    sites_df, fed_df = get_sites()
    df = fed_df.merge(sites_df, on='domain', how='left', suffixes=['_fed', '_sites'])
    # remove domains that aren't from the executive branch
    df = df[df['Domain Type'] == 'Federal Agency - Executive']
    # fill nulls in the site column with the domain and tld from the current federal csv
    df['site'] = df['site'].fillna(df['domain'] + "." + df['tld_fed'])
    df = df.drop_duplicates(subset=['site'])

    blacklist_terms = ['dev', 'test', 'staging', 'webmail', 'intranet', 'gopher', 'beta', 'ftp', 
                       'smtp', 'preprod', 'mail2', 'fas.my.salesforce', 'uccams', 'gitlab', 'github']
    df = df[~df['site'].str.contains("|".join(blacklist_terms))]

    df['constructed_url'] = df.apply(construct_url, axis = 1)

    df['schematized_url'] = df['constructed_url'].apply(schematize_url)
    df = df.drop_duplicates(subset=['schematized_url'])

    results = {k:None for k in df['schematized_url'].tolist()}
    n_domains = df.shape[0]
    print(f"Finding the routeable url for each of {n_domains} domains. This will take awhile...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        future_to_url = {executor.submit(get_routeable_url, url): url for url in results}
        
        for future in tqdm(concurrent.futures.as_completed(future_to_url)):
            url = future_to_url[future]
        
            try:
                routeable_url = future.result()
                results[url] = routeable_url  
            except Exception as exc:
                print('%r generated an exception: %s' % (url, exc))
    
    print("Done finding the routeable urls. Almost done now...")

    df['routeable_url'] = df['schematized_url'].map(results)
    df = df[~df.routeable_url.isnull()]
    df = df[~df.routeable_url.duplicated()]
    df = df[df['routeable_url']!='timeout']

    cols = ['Domain Type', 'Agency', 'Organization', 'routeable_url']
    df = df[cols]

    parsed_urls = df['routeable_url'].apply(lambda x: tldextract.extract(x)).apply(pd.Series)
    parsed_urls.columns = ['subdomain', 'domain', 'tld']
    parsed_urls.subdomain = parsed_urls.subdomain.replace('www','')
    df = pd.concat([df, parsed_urls], axis=1)

    df = df[~df['routeable_url'].str.endswith('ecpic.gov/')]

    df = df.drop_duplicates(subset=df.columns.difference(['routeable_url']))

    df = df[df['routeable_url']!='https://helix1-redirect.uspto.gov/']

    df.subdomain = df.subdomain.str.replace("www.",'')

    df = df.drop_duplicates(subset=['subdomain', 'domain', 'tld'])

    df[['Agency', 'Organization']] = df.apply(rename_rows,axis=1).apply(pd.Series)
    
    df.to_csv('domains.csv', index=False)

    print("All done!")
