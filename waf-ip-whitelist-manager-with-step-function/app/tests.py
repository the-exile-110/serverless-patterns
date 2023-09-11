from app import lambda_handler


add_event = {
    "ip": "192.168.1.1/32",
    "action": "add",
    "grade_id": "1"
}

update_event = {
    "ip": "192.168.1.2/32",
    "old_ip": "192.168.1.1/32",
    "action": "update",
    "grade_id": "1"
}

delete_event = {
    "ip": "192.168.1.1/32",
    "action": "delete",
    "grade_id": "1"
}


# print(lambda_handler(add_event, {}))

print(lambda_handler(delete_event, {}))