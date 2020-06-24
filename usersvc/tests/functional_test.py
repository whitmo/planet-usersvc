import requests
from .test_app import user_record, broken_record

new_record = user_record.copy()

def report(title, resp):
    print(">>> {}".format(title))
    try:
        json = resp.json()
    except Exception:
        json = ''
    print("%s %s" % (resp.status_code, json))
    print()

def exercise():
    resp = requests.post("http://0.0.0.0:6543/users", json=broken_record)
    report("Create user, invalid record", resp)

    resp = requests.post("http://0.0.0.0:6543/users", json=user_record)
    report("Create user, non-existant group", resp)

    new_record['groups'] = []
    resp = requests.put("http://0.0.0.0:6543/users/sue", json=new_record)
    report("Update, no user found", resp)

    resp = requests.get("http://0.0.0.0:6543/users/sue")
    report("Get user, none found", resp)

    resp = requests.post("http://0.0.0.0:6543/groups", json=dict(name="admin"))
    report("Create group admin", resp)

    resp = requests.post("http://0.0.0.0:6543/users", json=user_record)
    report("Create user", resp)

    resp = requests.get("http://0.0.0.0:6543/users/sue")
    report("Get user sue", resp)

    resp = requests.post("http://0.0.0.0:6543/groups", json=dict(name="green"))
    report("Create second group green", resp)

    new_record['groups'] = ['green', 'admin']
    resp = requests.put("http://0.0.0.0:6543/users/sue", json=new_record)
    report("Update user: sue", resp)

    resp = requests.get("http://0.0.0.0:6543/users/sue")
    report("Get user", resp)

    resp = requests.get("http://0.0.0.0:6543/groups/green")
    report("List users for group green", resp)

    new_record['groups'] = ['green']
    resp = requests.put("http://0.0.0.0:6543/users", json=new_record)
    report("Update user record: remove group admin", resp)

    resp = requests.get("http://0.0.0.0:6543/groups/admin")
    report("List users for group admin", resp)

    resp = requests.put("http://0.0.0.0:6543/groups/admin", json=['sue'])
    report("Add user sue to admin group", resp)

    resp = requests.get("http://0.0.0.0:6543/groups/admin")
    report("List users for group admin", resp)

    resp = requests.get("http://0.0.0.0:6543/users/sue")
    report("Check if sue has admin", resp)

    resp = requests.delete("http://0.0.0.0:6543/groups/admin")
    report("Delete admin group", resp)

    resp = requests.get("http://0.0.0.0:6543/users/sue")
    report("Check if sue has admin", resp)

    resp = requests.delete("http://0.0.0.0:6543/groups/admin")
    report("Delete deleted admin group", resp)

    resp = requests.delete("http://0.0.0.0:6543/users/nonexistent")
    report("Delete nonexistent", resp)

    resp = requests.delete("http://0.0.0.0:6543/users/sue")
    report("Delete sue", resp)

    resp = requests.get("http://0.0.0.0:6543/groups/green")
    report("List users for group green", resp)
