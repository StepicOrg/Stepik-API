var CLIENT_ID = 'n4mnzQGfDEfOhFixwBvLV2mZJJLvf86pzfMMiPF5'
var CLIENT_SECRET = '40ON9IPJRDAngUkVbGBTEjCBAwc2wB7lV8e71jJUPKabdKq6KBTUBKb1xGkh82KtAI1AqISrL3Zi4sTfhCBVh27YvlV6Y5klpXXV5loUWvuhMSRiN3HRZzVDO0fLBibv'
var API_HOST = 'https://stepik.org/'

var token = getStepikToken()

function getStepikToken(){
  tokenUrl = API_HOST + 'oauth2/token/';
  options = {
    'method': 'post',
    'headers': {
      'Authorization': 'Basic ' + Utilities.base64Encode(CLIENT_ID + ':' + CLIENT_SECRET)
    },
    'payload' : {
      'grant_type': 'client_credentials'
    },
  };
  response = UrlFetchApp.fetch(tokenUrl, options);
  return JSON.parse(response.getContentText()).access_token 
}

function getApiRequest(url){
  options = {
    'headers': {
      'Authorization': 'Bearer ' + token
    }
  };
  response = UrlFetchApp.fetch(API_HOST + 'api/' + url, options);
  return response.getContentText()
}

function fetchObjectsByPK(objectName, objectPK){  
  objectUrl = objectName + '/' + objectPK;
  return getApiRequest(objectUrl)
}

