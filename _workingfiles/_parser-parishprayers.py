from titlecase import titlecase
import csv


parsed = []

with open('_preparation-parishprayers.csv') as f:
	csvreader = csv.reader(f)
	next(csvreader)
	for row in csvreader:
		tags_and_attribution = [titlecase(_) for _ in row[2].split(',')]
		if row[5] != '': tags_and_attribution.append(row[5].replace('*', '').strip())

		title = titlecase(row[1].lower())
		tags = '\', \''.join(tags_and_attribution) # category
		order = row[3] # prayer
		content = row[4].replace('[', r'\[').replace(']', r'\]') # text
		attribution = row[5]
		parsed.append([order, tags, title, content, attribution])


# with open('_temp-parishprayers.txt') as f:
# 	prayer = 0
# 	new_category = True
# 	new_prayer = True
# 	parsed = []
# 	for index, line in enumerate(f):
# 		if line.strip() == '':
# 			# Blank line, skip
# 			pass



# 		if new_category:
# 			raw_category = line.strip().lower()
# 			attribution = None
# 			if raw_category.find(' (') != -1:
# 				attribution = titlecase(raw_category[(raw_category.find(' (') + 2):-1])
# 				category = raw_category[0:raw_category.find(' (')]
# 			else:
# 				category = raw_category
# 			categories = category.split(', ')
# 			category = '\', \''.join([titlecase(_) for _ in categories])
# 			new_category = False
# 		elif line == '\n':
# 			# Category break
# 			new_category = True
# 		else:
# 			# if line[0:(line.find('.') + 1)] == str(prayer + 1) + '.':
# 			if new_prayer:
# 				# Title line
# 				prayer += 1
# 				# title = titlecase(line[(line.find('. ') + 2):].strip().lower())
# 				title = titlecase(line.strip().lower())
# 				new_prayer = False
# 			else:
# 				# Content line
# 				text = line.strip().replace('[', r'\[').replace(']', r'\]').replace(r'\n', '\n')
# 				parsed.append([prayer, category, title, text, attribution])
# 				new_prayer = True

# print(parsed)
print(len(parsed))

for prayer in parsed:
	with open('temp/{}.md'.format(prayer[0]), 'w') as f:
		f.write('---\n')
		f.write('title: \'{}\'\n'.format(prayer[2]))

		# Attribution
		if prayer[4]:
			f.write('attribution: {}\n'.format(prayer[4]))

		f.write('layout: page\n')
		f.write('tags: [\'{}\']\n'.format(prayer[1]))
		f.write('source_order: {}\n'.format(prayer[0]))
		f.write('---\n')
		f.write('\n')
		f.write('{}\n'.format(prayer[3]))
