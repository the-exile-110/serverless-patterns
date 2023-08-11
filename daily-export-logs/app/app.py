import boto3
import datetime

s3 = boto3.client('s3')
logs = boto3.client('logs')

LOG_GROUP_NAMES = ['test-log-group-1', 'test-log-group-2']
BUCKET_NAME = 'test-bucket'


def export_logs_to_s3(log_group):
    end_time = datetime.datetime.now() - datetime.timedelta(days=90)
    start_time = datetime.datetime(1970, 1, 1)  # UNIX epoch start time
    safe_log_group = log_group.replace("/", "-")  # 替换 / 为 -

    response = logs.create_export_task(
        logGroupName=log_group,
        fromTime=int(start_time.timestamp() * 1000),
        to=int(end_time.timestamp() * 1000),
        destination=BUCKET_NAME,
        destinationPrefix=f'{safe_log_group}/before_{end_time.strftime("%Y-%m-%d")}'
    )
    return response['taskId']


def delete_logs(log_group):
    ninety_days_ago_timestamp = int((datetime.datetime.now() - datetime.timedelta(days=90)).timestamp() * 1000)
    streams = logs.describe_log_streams(logGroupName=log_group)

    for stream in streams['logStreams']:
        # 删除那些最后的事件发生在90天前的日志流
        if 'lastEventTimestamp' in stream and stream['lastEventTimestamp'] <= ninety_days_ago_timestamp:
            logs.delete_log_stream(logGroupName=log_group, logStreamName=stream['logStreamName'])


def lambda_handler(event, context):
    for log_group in LOG_GROUP_NAMES:
        export_logs_to_s3(log_group)
        delete_logs(log_group)


if __name__ == '__main__':
    lambda_handler(None, None)
