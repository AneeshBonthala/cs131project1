import time

def gcdOfString(str1, str2):
	lst1, lst2 = list(str1), list(str2)
	shorter = lst1 if len(lst1) < len(lst2) else lst2
	ans = [s for s in shorter]
	for i in range(len(ans)):
		if ans * (len(lst1)//len(ans)) == lst1:
			if ans * (len(lst2)//len(ans)) == lst2:
				break
		ans.pop()
	return ''.join(ans)

start_time = time.time()
gcdOfString('TAUXXTAUXXTAUXXTAUXXTAUXXTAUXXTAUXXTAUXXTAUXXTAUXXTAUXXTAUXXTAUXXTAUXXTAUXXTAUXXTAUXX', 'TAUXXTAUXXTAUXXTAUXXTAUXXTAUXXTAUXXTAUXXTAUXX')
end_time = time.time()

print('Execution time:', start_time - end_time)