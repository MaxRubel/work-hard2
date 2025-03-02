class LinkedList():
    def __init__(self):
        self.length = 0
        self.head = None

    def append(self, node):
        if self.head == None:
            self.head = node
            self.length+=1
        else:
            current = self.head

            while current.next:
                current = current.next

            current.next = node
            self.length+=1

    def prepend(self, node):
        node.next = self.head
        self.head = node
        self.length+=1

    def display(self):
        if self.head == None:
            print("Error - this list is empty")
            return
        else:
            current = self.head
            string = "head"
            while current:
                if current.next:
                    string += "[" + current.data + "]--> "
                else:
                    string += "[" + current.data + "]tail"
                current = current.next
            print(string)
            print("list length is: ", self.length)

    def insert_at_pos(self, pos, node):
        if pos < 1 or pos > self.length + 1:
            print("Error - Position is out of bounds")
            return

        if pos == 1:
            node.next = self.head
            self.head = node
        else:
            current = self.head
            for i in range(1, pos - 1):
                current = current.next
            
            node.next = current.next
            current.next = node

        self.length += 1

    def increment(self, data):
        if self.length <= 1:
            print("The list is too small to increment")

        if self.head.data == data:
            next_node = self.head.next
            self.head.next = next_node.next
            next_node.next = self.head
            self.head = next_node
            return
        
        prev = self.head
        current = self.head.next

        while current:
            if current.data == data:
                if not current.next:
                    print("can't increment last item")
                    return
                next_node = current.next
                current.next = next_node.next
                prev.next = next_node
                next_node.next = current
                return
        
            prev = prev.next
            current = current.next

        print("item with that data not found")


    def decrement(self, data):
        if self.length <= 1:
            print("cannot decrement. list is too small")
            return
        if self.head.data == data:
            print("cannot decrement first item")

        current = self.head.next
        prev = self.head
        prev2 = None

        while current:
            if current.data == data:
                if prev2:
                    prev.next = current.next
                    prev2.next = current
                    current.next = prev
                    return
                else:
                    self.head.next = current.next
                    current.next = self.head
                    self.head = current
                    return
            current = current.next
            prev2 = prev
            prev = prev.next
            

    def delete(self, data):
        if self.head == None:
            print("error - this list is empty")
            return
        else:
            current = self.head
            while current.next:
                if current.next.data == data:
                    current.next = current.next.next
                    return
                current = current.next
                    
class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

    def __repr__(self) -> str:
        return f"[{self.data}]-->"

def print_list(ll):
    if ll.head == None:
        print("Error - this list is empty")
        return
    else:
        current = ll.head
        string = "head"
        while current:
            if current.next:
                string += "[" + current.data + "]--> "
            else:
                string += "[" + current.data + "]tail"
            current = current.next
        print(string)

my_list = LinkedList()

my_list.append(Node("1st"))
my_list.append(Node("2nd"))
my_list.append(Node("3rd"))
my_list.insert_at_pos(4, Node("inserted"))

# my_list.increment("3rd")
my_list.increment("2nd")
my_list.increment("2nd")

my_list.display()

