import time,json,os

class history_node:
    def __init__(self,time_point,image_path,text,text_len):
        self.time_point = time_point
        self.image_path = image_path
        self.text = text
        self.text_len = text_len
        self.left = None
        self.right = None
class history_bst:
    def __init__(self):
        self.root = None
        self.save_path = "history.json"
        self.load_from_file()

    def my_insert(self,node,new_node):
        if new_node.time_point < node.time_point:
            if node.left == None :
                node.left = new_node
            else:
                self.my_insert(node.left,new_node)
        else:
            if node.right == None:
                node.right = new_node
            else:
                self.my_insert(node.right,new_node)
                
    def add_history(self,image_path,text):
        tp = time.time()
        text_len = len(text.strip())
        new_node = history_node(tp,image_path,text,text_len)
        if self.root == None:
            self.root =new_node
        else:
            self.my_insert(self.root,new_node)
        self.save_to_file()

    def inorder(self,node,res_list):
        if node == None:
            return
        self.inorder(node.left,res_list)
        res_list.append({
            "time_point":node.time_point,
            "image_path":node.image_path,
            "text":node.text,
            "text_len":node.text_len
        })
        self.inorder(node.right,res_list)

    def get_history(self):
        res=[]
        self.inorder(self.root,res)
        return res

    def search(self,node,start,end,res_list):
        if node == None:
            return
        if start <= node.time_point <= end:
            res_list.append({
                "time_point": node.time_point,
                "image_path": node.image_path,
                "text":node.text,
                "text_len":node.text_len
            })
            self.search(node.left,start,end,res_list)
            self.search(node.right,start,end,res_list)
        elif node.time_point > end:
            self.search(node.left,start,end,res_list)
        else:
            self.search(node.right,start,end,res_list)
    
    def search_by_time_range(self, start_tp,end_tp):
        res = []
        self.search(self.root,start_tp,end_tp,res)
        return res

    def search_keyword(self, node, keyword, res_list):
        if node == None:
            return
        lower_text = node.text.lower()
        lower_key = keyword.lower()
        if lower_key in lower_text:
            res_list.append({
                "time_point": node.time_point,
                "image_path": node.image_path,
                "text": node.text,
                "text_len": node.text_len
            })
        self.search_keyword(node.left, keyword, res_list)
        self.search_keyword(node.right, keyword, res_list)

    def search_by_keyword(self, keyword):
        res = []
        self.search_keyword(self.root, keyword, res)
        return res

    def save_to_file(self):
        records = self.get_history()
        try:
            with open(self.save_path, 'w', encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            print("历史记录已经写入")
        except Exception as err:
            print("保存失败，原因：", err)

    def load_from_file(self):
        if not os.path.exists(self.save_path):
            return
        try:
            with open(self.save_path, 'r', encoding="utf-8") as f:
                records = json.load(f)
            self.root = None
            for item in records:
                new_node = history_node(
                    item["time_point"],
                    item["image_path"],
                    item["text"],
                    item["text_len"]
                )
                if self.root is None:
                    self.root = new_node
                else:
                    self.my_insert(self.root, new_node)
            print(f"成功读取{len(records)}条历史记录")
        except Exception as err:
            print("读取历史文件失败：", err)
            self.root = None

history_tree = history_bst()