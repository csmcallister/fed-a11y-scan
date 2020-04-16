
def rename_rows(row):  # noqa: C901
    """Renames agencies and organizations; applied to pandas df
    """    
    agency = row['Agency'].strip()
    org = row['Organization'].strip()
    
    if 'Corporation for National' in agency:
        agency = 'Corporation for National and Community Service'
        if 'General' in org:
            org = 'Office Of Inspector General'
            
    elif agency == 'U.S. Department of Agriculture':
        agency = 'Department of Agriculture'
        if 'Forest Service' in org and 'Sensing' not in org:
            org = 'Forest Service'
        elif org == 'USDA':
            org = 'Department of Agriculture'
        elif 'OCIO' in org:
            org = 'Office of the Chief Information Officer'
        elif 'NAL' in org:
            org = 'National Agricultural Library'
            
    elif 'Department of State' in agency:
        agency = 'Department of State'
        if 'General' in org:
            org = 'Office Of Inspector General'
        elif 'ASEAN' in org:
            org = 'ASEAN Connect'
        elif 'of State' in org:
            org = 'Department of State'
    
    elif 'Federal Housing Finance Agency' in agency:
        agency = 'Federal Housing Finance Agency'
        if 'General' in org:
            org = 'Office Of Inspector General'
            
    elif 'United States Postal Service' in agency:
        agency = 'United States Postal Service'
        if 'General' in org:
            org = 'Office Of Inspector General' 
    
    elif agency == 'Department of Education':
        org = 'Department of Education'
        
    elif agency == 'Broadcasting Board of Governors':
        org = 'Broadcasting Board of Governors'
    
    elif agency == 'Department of Justice':
        if 'Alcohol' in org or 'ATF' in org:
            org = 'Bureau of Alcohol, Tobacco, Firearms and Explosives'
        elif 'DEA' in org:
            org = 'Drug Enforcement Agency'
        elif 'Bureu' in org or org == 'FBI':
            org = 'Federal Bureau of Investigation'
        elif org == 'U.S. Department of Justice, BI, Domestic Security Alliance Council (DSAC)':  # noqa: E501
            org = 'Domestic Security Alliance Council'
        elif 'Office of Justice Programs' in org or 'OJP' in org:
            org = 'Office of Justice Programs'
        elif 'CJIS' in org:
            org = 'Criminal Justice Information Services'     
        elif 'Intergovernemental' in org:
            org = 'Institute for Intergovernemental Research' 
        elif 'RCFL' in org:
            org = 'Regional Computer Forensics Laboratory'
        elif 'Criminal Division' in org:
            org = 'Criminal Division'
        elif 'Office of e-Government' in org:
            org = 'Office of e-Government'
        elif 'Department of Justice' in org:
            org = 'Department of Justice'
    
    elif agency == 'Department of Veterans Affairs':
        if org == 'U.S. Department of Veterans Affairs':
            org = 'Department of Veterans Affairs'
     
    elif agency == 'National Archives and Records Administration':
        if org == 'NARA' or org == 'U.S. National Archives and Records Administration':  # noqa: E501
            org = 'National Archives and Records Administration'
    
    elif agency == 'Environmental Protection Agency':
        if org == 'United Sates Environmental Protection Agency':
            org == 'Environmental Protection Agency'
            
    elif agency == 'Department of Commerce':
        if 'Standards' in org:
            org = 'National Institute of Standards & Technology'
        elif 'MBDA' in org:
            org = 'Minority Business Development Agency'
        elif 'NASA' in org:
            agency = 'National Aeronautics and Space Administration'
            org = 'NASA Goddard Space Flight Center'
        elif 'USPTO' in org:
            org = 'Patent and Trademark Office'
        elif org == 'ECONOMIC DEVELOPMENT ADMINISTRATION':
            org = org.title()
        elif 'NCDC' in org:
            org = 'NOAA National Climatic Data Center'
        elif 'Department of Commerce' in org:
            org = 'Department of Commerce'
            
    elif agency == 'Department of Labor':
        if 'OCIO' in org:
            org = 'Office of the Chief Information Officer'
        elif 'ETA' in org:
            org = 'Employment and Training Administration'
        
    elif agency == 'General Services Administration':
        if 'TTS' in org:
            org = 'Technology Transformation Service'
        elif '18F' in org:
            org = '18F'
        elif 'OSCIT' in org:
            org = 'Office of Citizen Services Innovative Technologies'
        elif 'High-Performance' in org:
            org = 'Office of Federal High-Performance Green Buildings'
        elif 'STEERING' in org:
            org = org.title()
        elif 'OAS' in org:
            org = 'Office of Administrative Services'
        elif 'FAI' in org:
            org = 'Federal Acquisition Institute'
        elif 'OGP' in org:
            org = 'Office of Government-wide Policy'
        elif 'FAS' in org:
            org = 'Federal Acquisition Service'
        elif 'IAE' in org:
            org = 'Integrated Acquisition Environment'
        elif 'General Services Administration' in org or org == 'GSA':
            org = 'General Services Administration'
    
    elif agency == 'Consumer Product Safety Commission':
        org = 'Consumer Product Safety Commission'
    
    elif agency == 'Federal Deposit Insurance Corporation':
        org = 'Federal Deposit Insurance Corporation'
    
    elif agency == 'United States AbilityOne':
        org = 'Committee for Purchase From People Who are Blind or Severely Disabled'  # noqa: E501
    
    elif agency == 'Department of Housing and Urban Development':
        if 'Policy Development' in org:
            org = 'Office of Policy Development and Research'
        elif 'Urban Development' in org:
            org = 'Department of Housing and Urban Development'
            
    elif agency == 'Council of Inspectors General on Integrity and Efficiency':
        org = 'Council of Inspectors General on Integrity and Efficiency'
    
    elif agency == 'Department of Health and Human Services':
        if org == 'AHRQ':
            org = 'Agency for Healthcare Research and Quality'
        elif 'Heart' in org:
            org = 'National Heart, Lung & Blood Institute'
        elif 'SAMHSA' in org:
            org = 'Substance Abuse and Mental Health Services Administration'
        elif 'NIAAA' in org:
            org = 'National Institute on Alcohol Abuse and Alcoholism'
        elif 'LIbrary' in org:
            org = 'National Library of Medicine'
        elif 'NCI' in org:
            org = 'National Cancer Institute'
        
        elif 'DHHS' in org or org == 'Dept of Health and Human Services' or org == 'HHS' or 'Department of Health' in org:  # noqa: E501
            org = 'Department of Health and Human Services'
    
    elif agency == 'Office of Personnel Management':
        if org == 'U.S. Office of Personnel Management':
            org = 'Office of Personnel Management'
    
    elif agency == 'Department of the Treasury':
        if 'Citizens Coinage Advisory Committee' in org:
            org = 'Citizens Coinage Advisory Committee'
        elif 'Mint' in org:
            org = 'Mint'
        elif 'BEP' in org:
            org = 'Bureau of Engraving and Printing'
        elif 'OCC' in org:
            org = 'Comptroller of the Currency'
        elif org == 'General Services Administration, Office of Citizen Services':  # noqa: E501
            agency = 'General Services Administration'
            org = 'Office of Citizen Services'
        elif 'FINCEN' in org:
            org = 'FinCEN'
        elif 'FINCEN' in org:
            org = 'Financial Stability Oversight Council'
        elif 'IRS' in org:
            org = 'Internal Revenue Service'
        elif org == 'Department of the Treasury - FS':
            org = 'Bureau of the Fiscal Service'
        elif 'BPD' in org:
            org = 'Bureau of the Public Debt'
        elif 'FMS' in org:
            org = 'Financial Management Service'
        elif 'OCIO' in org:
            org = 'Office of the Chief Information Officer'
        elif 'OFR' in org:
            org = 'Office of Financial Research'
        elif 'OTS' in org:
            org = 'Office of Thrift Supervision'
        elif 'CDFI' in org:
            org = 'Community Development Financial Institutions Fund'
        elif org == 'Treasury' or 'Department of the Treasury' in org:
            org = 'Department of the Treasury'
    
    elif agency == 'National Credit Union Administration':
        org = 'National Credit Union Administration'
    
    elif agency == 'Department of Transportation':
        if org == 'OCIO':
            org = 'Office of the Chief Information Officer'
        elif 'AMi400' in org:
            org = 'The Federal Aviation Administration, Telecommunications Unit'  # noqa: E501
        elif 'MMAC' in org:
            org = 'Mike Monroney Aeronautical Center'
        elif 'NHTSA' == org:
            org = 'National Highway Traffic Safety Administration'
        elif 'Department of Transportation' in org:
            org = 'Department of Transportation'
    
    elif agency == 'Department of the Interior':
        if 'OIG' in org:
            org = 'Office of Inspector General'
        elif 'NWRC' in org:
            org = 'Wetland and Aquatic Reserch Center'
        elif 'Volcano Science Center' in org:
            org = 'Volcano Science Center'
        elif 'Survey' in org:
            org = 'US Geological Survey'
        elif 'Fish and Wildlife' in org:
            org = 'Fish and Wildlife Service'
        elif 'Department of Interior' == org:
            org = 'Department of the Interior'
    
    elif agency == 'Department of Homeland Security':
        if 'Office of the Chief Information Officer' in org:
            org = 'Office of the Chief Information Officer'
        elif org == 'USCIS':
            org = 'US Citizenship and Immigration Services'
        elif org == 'US-CERT':
            org = 'United States Computer Emergency Readiness Team'
        elif org == 'FEMA':
            org = 'Federal Emergency Management Agency'
        elif org == 'TSA CPO':
            org = 'Transportation Security Administration, Credentialing Program Office'  # noqa: E501
    
    elif agency == 'Nuclear Regulatory Commission':
        org = 'Nuclear Regulatory Commission'
    
    elif agency == 'U.S. Agency for International Development':
        if org == 'USAID/GH.CECA':
            org = 'Center on Children in Adversity'
        elif 'Agency for International Development' in org:
            org = 'U.S. Agency for International Development'
    
    elif agency == 'Department of Energy':
        if org == 'US DEPARTMENT OF ENERGY':
            org = 'Department of Energy'
        elif org == 'EERE':
            org = 'Office of Energy Efficiency and Renewable Energy'
        elif org == 'OSTI':
            org = 'Office of Scientific and Technical Information'
        elif org == 'ORAU':
            org = 'Oak Ridge Associated Universities'
        elif org == 'NNSA':
            org = 'National Nuclear Security Administration'
        elif 'Office of the CIO' in org:
            org = 'Office of the Chief Information Officer'
    
    elif agency == 'Department of Defense':
        if org == 'NRO':
            org = 'National Reconnaissance Office'
        elif org == 'MCTFT':
            org = 'Multijurisdictional Counterdrug Task Force Training Program'
        elif org == 'NSA':
            org = 'National Security Agency'
        elif org == 'OFFICE OF WARRIOR CARE POLICY':
            org = org.title()
    return agency, org
