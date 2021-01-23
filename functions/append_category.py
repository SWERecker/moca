import pymongo

client = pymongo.MongoClient(host='localhost', port=27017)

db1 = client['moca']
gkw = db1['group_keyword']

append_all = True
group_id = 708729447

if append_all:
    cursor = gkw.find()
else:
    cursor = gkw.find({"group": group_id})

to_append_data = {
    "高木美佑": "来点高木美佑|来点美佑|来点大额头"
}

if __name__ == "__main__":
    for d in cursor:
        group_keyword: dict = d['keyword']
        group: int = d['group']
        group_keyword.update(to_append_data)
        res = gkw.update_one({'group': group}, {'$set': {'keyword': group_keyword}})
        print(f'Modified Group = {group}, Count = {res.modified_count}')
