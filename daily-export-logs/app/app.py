import time
import boto3
import datetime

s3 = boto3.client('s3')
logs = boto3.client('logs')

LOG_GROUP_NAMES = ['/aws/lambda/SSTBootstrap-CustomS3AutoDeleteObjectsCustomResour-cCZrLAUydYCe']
BUCKET_NAME = 'qq-tmp'
ROTATION_DAYS = 15


def export_logs_to_s3(log_group):
    end_time = datetime.datetime.now() - datetime.timedelta(days=ROTATION_DAYS)
    start_time = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)  # UNIX epoch start time
    safe_log_group = log_group[1:].replace("/", "-") if log_group.startswith("/") else log_group.replace("/", "-")  # Replace slashes with dashes for S3 prefix

    print(f"Exporting logs from {log_group} to S3 bucket {BUCKET_NAME} with prefix {safe_log_group}/before_{end_time.strftime('%Y-%m-%d')}")

    response = logs.create_export_task(
        logGroupName=log_group,
        fromTime=int(start_time.timestamp() * 1000),
        to=int(end_time.timestamp() * 1000),
        destination=BUCKET_NAME,
        destinationPrefix=f'{safe_log_group}/before_{end_time.strftime("%Y-%m-%d")}'
    )

    task_id = response['taskId']

    # Wait for export task to complete
    while True:
        response = logs.describe_export_tasks(taskId=task_id)
        status = response['exportTasks'][0]['status']['code']
        if status == 'COMPLETED':
            break
        elif status == 'FAILED':
            print(f"Export task {task_id} failed!")
            return
        time.sleep(10)  # Wait for 10 seconds before checking again

    return task_id


def delete_logs(log_group):
    ninety_days_ago_timestamp = int((datetime.datetime.now() - datetime.timedelta(days=ROTATION_DAYS)).timestamp() * 1000)
    streams = logs.describe_log_streams(logGroupName=log_group)

    for stream in streams['logStreams']:
        # Delete the log stream if it has not been updated in the last 90 days
        if 'lastEventTimestamp' in stream and stream['lastEventTimestamp'] <= ninety_days_ago_timestamp:
            logs.delete_log_stream(logGroupName=log_group, logStreamName=stream['logStreamName'])
            print(f"Deleted log stream {stream['logStreamName']} in log group {log_group}")


def lambda_handler(event, context):
    for log_group in LOG_GROUP_NAMES:
        export_logs_to_s3(log_group)
        delete_logs(log_group)


if __name__ == '__main__':
    lambda_handler(None, None)
