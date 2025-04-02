# # LinkedList Data Structure...

# class Node:
#     def __init__(self, item):
#         self.item = item
#         self.next = None

# class LinkedList:
#     def __init__(self):
#         self.head = None


# linkedList = LinkedList()

# elementOne = Node(1)
# elementTwo = Node(2)
# elementThree = Node(3)

# linkedList.head = elementOne
# elementOne.next = elementTwo
# elementTwo.next = elementThree

# while linkedList.head != None:
#     print(linkedList.head.item, end=" ")
#     linkedList.head = linkedList.head.next

# # Queue Data Structure
# class Queue:
#     def __init__(self):
#         self.queue = []

    
#     def enquee(self, item):
#         self.queue.append(item)

#     def dequee(self):
#         if len(self.queue) < 1:
#             return "Queue is Empty"
#         self.queue.pop(0)
    
#     def peek(self):
#         return self.queue[0]


# queueInstance = Queue()

# queueInstance.enquee("Coding")
# queueInstance.enquee("Washing")

# print(queueInstance.dequee())
# print(queueInstance.dequee())
# print(queueInstance.dequee())
# queueInstance.enquee("Football")
# print(queueInstance.queue)


# class MySet:
#     def __init__(self):
#         self.set = [6, 2, 3]
    
#     def add(self, element):
#         if not self.has(element):
#             self.set.append(element)


#     def has(self, element):
#         if self.set.index(element) == None:
#             return False
#         return True


# setInstance = MySet()
# setInstance.add(8)
