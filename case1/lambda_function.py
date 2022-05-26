import json
import boto3
import logging
from custom_encoder import CustomEncoder

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb_table = "articles-inventory"
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(dynamodb_table)

get_method = 'GET'
post_method = 'POST'
patch_method = 'PATCH'
delete_method = 'DELETE'
health_path = '/health'
article_path = '/article'
articles_path = '/articles'


def lambda_handler(event, context):
    logger.info(event)
    http_method = event['httpMethod']
    path = event['path']
    if http_method == get_method and path == health_path:
        response = build_response(200)
    elif http_method == get_method and path == article_path:
        response = read_article(event['queryStringParameters']['articleId'])
    elif http_method == get_method and path == articles_path:
        response = read_articles()
    elif http_method == post_method and path == article_path:
        response = create_article(json.loads(event['body']))
    elif http_method == patch_method and path == article_path:
        request_body = json.loads(event['body'])
        response = update_article(
            request_body['articleId'],
            request_body['updateKey'],
            request_body['updateValue']
        )
    elif http_method == delete_method and path == article_path:
        request_body = json.loads(event['body'])
        response = delete_article(request_body['articleId'])
    else:
        response = build_response(404, 'Not Found')

    return response


def read_article(articleId):
    try:
        response = table.get_item(
            Key={
                'articleId': articleId
            }
        )
        if 'Item' in response:
            return build_response(200, response['Item'])
        else:
            return build_response(
                404, {'Message': 'ArticleId: %s not found' % articleId}
            )
    except:
        logger.exception('Cant read item in dynamodb table!')


def read_articles():
    try:
        response = table.scan()
        result = response['Items']

        while 'LastEvaluatedKey' in response:
            response = table.scan(
                ExclusiveStartKey=response('LastEvaluatedKey')
            )
            result.extend(response['Items'])

        body = {
            'articles': response
        }
        return build_response(200, body)
    except:
        logger.exception('Cant read items in dynamodb table!')


def create_article(request_body):
    try:
        table.put_item(Item=request_body)
        body = {
            'Operation': 'SAVE',
            'Message': 'SUCCESS',
            'Item': request_body
        }
        return build_response(200, body)
    except:
        logger.exception('Cant delete item in dynamodb table!')


def update_article(articleId, updateKey, updateValue):
    try:
        response = table.update_item(
            Key={
                'articleId': articleId
            },
            UpdateExpression='set %s = :value' % updateKey,
            ExpressionAttributeValues={
                ':value': updateValue
            },
            ReturnValues='UPDATED_NEW'
        )
        body = {
            'Operation': 'UPDATE',
            'Message': 'SUCCESS',
            'UpdateAttributes': response
        }
        return build_response(200, body)
    except:
        logger.exception('Cant update item in dynamodb table!')


def delete_article(articleId):
    try:
        response = table.delete_item(
            Key={
                'articleId': articleId
            },
            ReturnValues='ALL_OLD'
        )
        body = {
            'Operation': 'DELETE',
            'Message': 'SUCCESS',
            'DeleteItem': response
        }
        return build_response(200, body)
    except:
        logger.exception('Cant delete item in dynamodb table!')


def build_response(status_code, body=None):
    response = {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }
    }
    if body is not None:
        response['body'] = json.dumps(body, cls=CustomEncoder)
    return response