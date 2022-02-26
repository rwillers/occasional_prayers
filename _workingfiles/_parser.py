from titlecase import titlecase

with open('_temp.txt') as f:
	prayer = 0
	new_category = True
	new_prayer = True
	parsed = []
	for index, line in enumerate(f):
		if new_category:
			category = titlecase(line.strip().lower())
			new_category = False
		elif line == '\n':
			# Category break
			new_category = True
		else:
			# if line[0:(line.find('.') + 1)] == str(prayer + 1) + '.':
			if new_prayer:
				# Title line
				prayer += 1
				# title = titlecase(line[(line.find('. ') + 2):].strip().lower())
				title = titlecase(line.strip().lower())
				new_prayer = False
			else:
				# Content line
				text = line.strip().replace('[', r'\[').replace(']', r'\]')
				parsed.append([prayer, category, title, text])
				new_prayer = True

# print(parsed)
print(len(parsed))

for prayer in parsed:
	with open('../acna2019collects/{}.md'.format(prayer[0]), 'w') as f:
		f.write('---\n')
		f.write('title: {}\n'.format(prayer[2]))
		f.write('layout: page\n')
		f.write('tags: [\'{}\']\n'.format(prayer[1]))
		f.write('source_order: {}\n'.format(prayer[0]))
		f.write('---\n')
		f.write('\n')
		f.write('{}\n'.format(prayer[3]))
