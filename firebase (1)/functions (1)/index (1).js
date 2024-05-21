const functions = require('firebase-functions');
const request = require('request');

// Create and Deploy Your First Cloud Functions
// https://firebase.google.com/docs/functions/write-firebase-functions


const sendUpdatedThreadData = function (baseUrl, threadId, data) {
  return request.patch({
    url: baseUrl + '/api/chats/firebase/threads/' + threadId + '/',
    json: data,
    headers: {
      'x-token': functions.config().api.key
    }
  }).on('error', (err) => {
    console.error(err);
  });
};

const addUserToThread = function (baseUrl, threadId, uuid, role) {
  return request.post({
    url: baseUrl + '/api/chats/firebase/threads/' + threadId + '/join/',
    json: {
      'user': uuid,
      'role': role,
    },
    headers: {
      'x-token': functions.config().api.key
    }
  }).on('error', (err) => {
    console.error(err);
  });
};

const sendNewMessage = function (baseUrl, threadId, messageId, data) {
  let requestData = {
    id: messageId,
    author: data.from
  };

  if (data.json_v2) {
    requestData.data = data.json_v2;
  } else if (data.meta) {
    requestData.data = data.meta;
  }

  return request.post({
    url: baseUrl + '/api/chats/firebase/threads/' + threadId + '/messages/',
    json: requestData,
    headers: {
      'x-token': functions.config().api.key
    }
  }).on('error', (err) => {
    console.error(err);
  });
};


const updateThreadLastMessage = function (pathPrefix, users, data, context, snapshot) {
    let promises = [];
    let messageData = {date: data.date};
    if (data.json_v2){
        messageData.json_v2 = data.json_v2;
    }
    if (data.meta){
        messageData.meta = data.meta;
    }

    for (let user of users) {
      let promise = snapshot.app.database('https://realtorx-89c5d.firebaseio.com').ref(
          '/' + pathPrefix + '/users/' + user + '/threads/' + context.params.threadId + '/lastMessage'
      ).set(messageData).catch(err => {console.error(err);});

      promises.push(promise);
    }

    return Promise.all(promises);
  };


let mapping = new Map();
mapping.set('staging', 'https://staging2.agentloop.us');
mapping.set('production', 'https://api.agentloop.us');
mapping.set('demo', 'https://demo.agentloop.us');


for (const [pathPrefix, baseUrl] of mapping.entries()) {
  const handleNewThreadUser = function (snapshot, context) {
    console.log(context.params.uuid + ' joined to thread ' + context.params.threadId);
    const data = snapshot.val();
    return addUserToThread(baseUrl, context.params.threadId, context.params.uuid, data.status);
  };

  const handleSetThreadHouse = function (snapshot, context) {
    console.log('House ' + snapshot.val() + ' was added to thread ' + context.params.threadId);
    return sendUpdatedThreadData(baseUrl, context.params.threadId, {house: snapshot.val()});
  };

  const handleNewMessage = function (snapshot, context) {
    console.log('Sending ' + context.params.messageId + ' message to thread ' + context.params.threadId);
    return sendNewMessage(baseUrl, context.params.threadId, context.params.messageId, snapshot.val());
  };

  const handleUpdateThreadLastMessage = function (snapshot, context) {
      const data = snapshot.val();
      const users = [data.from].concat(data.to);

      console.log('Updating ' + context.params.threadId + ' last message data for users ' + users.toString() + ' to ' + data.date);

      return updateThreadLastMessage(pathPrefix, users, data, context, snapshot);
  };

  let functionPostfix = pathPrefix.replace(/-/g, '_');

  exports['notifyNewThreadUser__' + functionPostfix] = functions.database.ref('/' + pathPrefix + '/threads/{threadId}/users/{uuid}').onCreate(handleNewThreadUser);
  exports['notifySetThreadHouse__' + functionPostfix] = functions.database.ref('/' + pathPrefix + '/threads/{threadId}/meta/house').onCreate(handleSetThreadHouse);
  exports['notifyNewMessage__' + functionPostfix] = functions.database.ref('/' + pathPrefix + '/threads/{threadId}/messages/{messageId}').onCreate(handleNewMessage);
  exports['updateThreadLastMessage_' + functionPostfix] = functions.database.ref('/' + pathPrefix + '/threads/{threadId}/messages/{messageId}').onCreate(handleUpdateThreadLastMessage);
}
