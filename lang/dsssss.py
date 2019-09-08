
class Stack :
	
	def __init__(self, contents=None):
		self.items = contents or []
	
	def __repr__(self):
	 	return str(self.items)
	
	def is_empty(self):
		return self.items == []
		
	def push(self,item):
		self.items.append(item)		
		
	def pop(self):
		return self.items.pop()
		
	def peek(self):
		return self.items[len(self.items)-1]
	
	def size(self):
		return len(self.items)
	
	def clear(self):
		self.items = []