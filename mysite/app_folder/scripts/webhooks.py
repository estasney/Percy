import requests


def register_webhook(api_key, hook_name, target_url, room_id, resource='messages', event='created', filter_=None):
    url = "https://api.ciscospark.com/v1/webhooks"
    s = requests.session()
    s.headers.update({'Content-type': 'application/json; charset=utf-8'})
    s.headers.update({'Authorization': api_key})

    if not filter_:
        filter_ = "roomId={}".format(room_id)
        filter_ += "&mentionedPeople=me"

    data = {'name': hook_name,
            'targetUrl': target_url,
            'resource': resource,
            'event': event,
            'filter': filter_}

    s.post(url, json=data)


# roomType — limit to a particular room type (such as direct or group)

