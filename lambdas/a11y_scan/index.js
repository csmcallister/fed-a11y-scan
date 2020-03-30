const AWS = require('aws-sdk');
const chromium = require('chrome-aws-lambda');
const moment = require('moment');
const pa11y = require('pa11y');

AWS.config.update({region: 'us-east-1'});

var s3 = new AWS.S3();
const bucket = process.env.BUCKET_NAME;

function isEmpty(obj) {
  for(var key in obj) {
      if(obj.hasOwnProperty(key))
          return false;
  }
  return true;
}

async function putResult(result, messageBody) {
  const agency = messageBody.Agency;
  const organization = messageBody.Organization;
  const domain = messageBody.domain;
  const subdomain = (messageBody.subdomain) ? messageBody.subdomain : '';
  const numberOfErrors = JSON.parse(result).issues.length.toString();
  const routeableUrl = messageBody.routeable_url;
  const scanDate = moment().format('Y-MM-DD');
  const prefix = `${agency}/${organization}`;
  const key = (subdomain) ? `${prefix}/${domain}/${subdomain}` : `${prefix}/${domain}`;
  
  const data = {
    'agency': agency,
    'organization': organization,
    'domain': domain,
    'subdomain': subdomain,
    'numberOfErrors' : numberOfErrors,
    'routeableUrl' : routeableUrl,
    'issues' : result,
    'scanDate': scanDate
  };

  const params = {
    Bucket: bucket,
    Key: `${key}.json`,
    Body: JSON.stringify(data),
    ContentType: 'application/json'
  };

  try {
    const response = await s3.upload(params).promise();
    console.log('Response: ', response);
    return response;
  } catch (error) {
      console.log(error);
  }
  return
};

async function runPa11y(domain, browser) {
  let result = null;
  let ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36';
  
  try {
    result = await pa11y(domain, { 
      standard: 'Section508',
      timeout: 50000, //be generous
      browser: browser,
      userAgent: ua
    });
    return JSON.stringify(result, null)
  
  } catch (error) {
      console.error(`FAILED TO SCAN ${domain}: \n ${error}`);
  };
};

exports.handler = async (event, context) => {
  //context.callbackWaitsForEmptyEventLoop = false;
  let result = null;
  let browser = null;
  let messageBody = null;
  let response = null;

  //batch size is currently set to 1, so index first body value
  try {
    messageBody = event.Records.map( i => JSON.parse(i.body))[0];
  } catch (error) {
    context.fail(error)
  }
   
  if (!messageBody) {
    return context.fail("No message body");
  }
  
  try {
    browser = await chromium.puppeteer.launch({
      args: chromium.args,
      defaultViewport: chromium.defaultViewport,
      executablePath: await chromium.executablePath,
      headless: chromium.headless
    });

    try {
      result = await runPa11y(messageBody.routeable_url, browser);
    } catch (error) {
      console.error(error)
      }

  } catch (error) {
      console.error(messageBody.routeable_url)
      return context.fail(error);
  
  } finally {
      if (browser !== null) {
        try { await browser.close(); } catch (e) { }
    }
  }

  if ( isEmpty(result) || !result ) {
    //former occurs when pages timeout; latter with other errors
    console.log("empty result")
    return context.succeed(result);
  } 
  
  try {
    response = await putResult(result, messageBody)
  } catch (error) {
      return context.fail(error)
  }
  return context.succeed();
};