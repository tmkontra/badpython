import csv
# import profanity_filter

# pf = profanity_filter.ProfanityFilter()

approvals = []
deletes = []
with open('./suggestions.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # clean = pf.is_clean(row['code'])
        c = ""
        msg = f"Suggestion {row['id']} {c}\n"
        msg += row['code']
        msg += "\n"
        print(msg)
        resp = input("What to do [Y/d/ ]")
        if resp == "Y":
            approvals.append(row['id'])
        elif resp == "d":
            deletes.append(row['id'])
        else:
            continue

print("Approvals\n%s"% ",".join(approvals))
print("Deletes\n%s" % ",".join(deletes))
