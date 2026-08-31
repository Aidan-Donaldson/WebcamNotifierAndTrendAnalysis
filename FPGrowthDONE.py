from Manager import GetEvents

class FPNode: 
    def __init__(self, alphabetSize):
        self.alphabetSize = alphabetSize
        self.child = [None] * alphabetSize
        self.occurence = None
        self.link = None
        self.parent = None
        self.supportCount = 0
    
    
    def Insert(self, occurences, freq = 1):
        current = self
        
        for index in occurences:
            if current.child[index] is None:
                newNode = FPNode(self.alphabetSize)
                current.child[index] = newNode
                current.child[index].occurence = index
                current.child[index].parent = current
            
            current.child[index].supportCount += freq
                
            current = current.child[index]
    
    
    def Lookup(self, occurences):
        head = occurences[0]
        tail = occurences[1:]
        
        if type(head) is not int:
            raise Exception("Invalid Node")
        elif head > self.alphabetSize - 1 or head < 0:
            raise Exception("Invalid Range")
        
        if self.child[head] is not None:
            if len(tail) > 0:
                node = self.child[head].Lookup(tail)
            else:
                node = self.child[head]
        else:
            return None
        return node
    

class FPTree:
    def __init__(self, alphabetSize, orderedFreq):
        self.alphabetSize = alphabetSize
        self.orderedFreq = orderedFreq
        self.root = FPNode(alphabetSize)
        self.headerTable = {}
        for i in orderedFreq:
            self.headerTable[i] = None
        
    def Insert(self, occurences, freq = 1):
        if occurences != []:  #Only ever adds empty when creating conditional FP trees
            self.root.Insert(occurences, freq)
            for pos, occurence in enumerate(occurences):
                targetNode = self.root.Lookup(occurences[:pos+1])
                if self.headerTable[occurence] is None:
                    self.headerTable[occurence] = targetNode
                elif targetNode.supportCount == freq:
                    nextNode = self.headerTable[occurence]
                    while nextNode.link is not None:
                        nextNode = nextNode.link
                    nextNode.link = targetNode
        self.root.supportCount += freq
                

def MappingKey(data):
    key = {}
    numEvents = 0
    array = []
    for record in data:
        array.append(record[0])

    numEvents = max(array)
    
    row = 0
    for record in data:
        col = 0
        for feature in record:
            if col == 0:
                key[feature] = feature-1
            
            if col == 1:
                DaysMonths = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30]
                day = int(feature[8:])
                month = int(feature[5:7])
                year = int(feature[0:4])
                extraDays = 0
                for i in range(month-1):
                    extraDays += DaysMonths[i]
                
                key[feature] = day+extraDays+numEvents-1
            
            if col == 2: #low performance when events fall on either side of an hour boundary
                scaledMinutes = int(feature[3:5])*100/60
                hourRound = round(scaledMinutes/100)
                hour = (int(feature[0:2]) + hourRound) %  24 # %24 so that 24:00 becomes 0:00
                key[feature] = hour+numEvents+366
                
            if col == 3:
                Days = {"Mon": 1, "Tue": 2, "Wed": 3, "Thu": 4, "Fri": 5, "Sat": 6, "Sun": 7}
                key[feature] = Days[feature] + numEvents + 23 + 366
            
            col += 1
        row += 1
        
    return key

def MapData(data, key):
    mappedData = []
    for row in range(len(data)):
        mappedData.append([])
        for col in range(len(data[row])):
            converted = key[data[row][col]]
            mappedData[row].append(converted)
    
    return mappedData        
        
def UnmapRules(associationRules, key):
    reversedKey = {val:key for key, val in key.items()}
    convertedRules = []
    for row, rule in enumerate(associationRules):
        convertedRules.append([])
        for part in range(2): #contains antecendent, consequent and confidence (ignored)
            partToList = list(associationRules[row][part])
            convertedPart = [reversedKey[value] for value in partToList]
            convertedRules[row].append(convertedPart)
        convertedRules[row].append(rule[-1]) # Re-add confidence
    
    return convertedRules
    

def OrderedFreqTable(data):
    freqTable = {}

    for occurenceId in range(ALPHABETSIZE):
        freqTable[occurenceId] = 0

    for record in data:
        for feature in record:
            freqTable[feature] = freqTable[feature] + 1

    orderedFreqTable = sorted(freqTable.items(), key=lambda item: item[1], reverse=True)
    return orderedFreqTable


def OrderedOccurences(occurences, orderedFreqTable):
    orderedOccurences = []
    orderedFreq = []
    supportThreshold = 2
    for i in orderedFreqTable:
        if i[1] > supportThreshold:
            orderedFreq.append(i[0])
            
    for occurence in occurences:
        relativeFreqs = [orderedFreq.index(feature) for feature in occurence if feature in orderedFreq]
        sortedRelFreqs = sorted(relativeFreqs)
        orderedOccurence = [orderedFreq[x] for x in sortedRelFreqs]
        orderedOccurences.append(orderedOccurence)
    return orderedOccurences, orderedFreq
    

def BuildTree(orderedFreq, formattedOccurences, freq = None):
    tree = FPTree(ALPHABETSIZE, orderedFreq)
    if freq is None:                                       #used for initial tree
        for path in formattedOccurences:
            tree.Insert(path)
    else:                                                  #Used for ConditionalFPTree
        for i, path in enumerate(formattedOccurences):
            tree.Insert(path, freq[i])
    return tree


def EventSupport(occurence, tree):
    total = 0
    loop = True
    nextNode = tree.headerTable[occurence]
    while loop == True:
        total += nextNode.supportCount
        if nextNode.link is not None:
            nextNode = nextNode.link
        else:
            loop = False

    return total


def GenerateConditionalPatternBase(tree, suffix):
    patternBases = []
    patternFreqs = []
    node = tree.headerTable[suffix] #May be None
    scanned = False
    while scanned == False:
        base = []
        support = node.supportCount
        parent = node.parent
        nextSubtree = node.link
        if nextSubtree is None:
            scanned = True
        subtreeScanned = False
        while subtreeScanned == False:
            if node.occurence != suffix:
                base.append(node.occurence)
            parent = node.parent
            node = parent
            if node.parent is None:
                subtreeScanned = True
        patternFreqs.append(support)
        patternBases.append(base)
        node = nextSubtree
        
    return patternBases, patternFreqs


def GenerateFrequentItemSet(tree, orderedFreq):
    itemset = []
    
    def loop(tree, postfix = []): #Post fix only used once recursion starts
        for suffix in tree.headerTable:
            tempDB, tempFreqs = GenerateConditionalPatternBase(tree, suffix)
            newDB = []
            for i, path in enumerate(tempDB):
                for x in range(tempFreqs[i]):
                    newDB.append(path)
            freqOrder = OrderedFreqTable(newDB)
            orderedConditionalOccurences, conditionalOrderedFreq = OrderedOccurences(tempDB, freqOrder)
            #print(orderedConditionalOccurences, tempFreqs, suffix, postfix)
            
            conditionalFPTree = BuildTree(conditionalOrderedFreq, orderedConditionalOccurences, tempFreqs)
            
            newPostfix = [suffix] + postfix
            support = conditionalFPTree.root.supportCount
            itemset.append([newPostfix, support])
            if len(conditionalOrderedFreq) > 0:
                loop(conditionalFPTree, newPostfix)
    loop(tree)
    
    return itemset


def FindAssociationRules(itemset, confidenceThreshold = 0.7): #Could be improved to generalise for more features and by including no-event data.
    rules = []
    def DetermineIfRule(antecendent, consequent, support):
        for items in itemset:
            testOccurences = set(items[0])
            if testOccurences == antecendent:
                testSupport = items[1]
                confidence = support / testSupport
                if confidence >= confidenceThreshold:
                    rules.append([antecendent, consequent, round(confidence, 2)])
                
    for items in itemset:
        occurences, support = items[0], items[1]
        length = len(occurences)
        if length > 1:
            #print(occurences)
            if length > 2:
                for pos in range(length):    
                    antecendent = set([occurences[pos]])
                    consequent = set(occurences).difference(antecendent)
                    DetermineIfRule(antecendent, consequent, support)
                    consequent = set([occurences[pos]])
                    antecendent = set(occurences).difference(consequent)
                    DetermineIfRule(antecendent, consequent, support)
                    
                    if length == 4:
                        for x in range(pos+1, length):
                            antecendent = set([occurences[pos]] + [occurences[x]])
                            consequent = set(occurences).difference(antecendent)
                            DetermineIfRule(antecendent, consequent, support)
            else:
                antecendent = set([occurences[0]])
                consequent = set([occurences[1]])
                DetermineIfRule(antecendent, consequent, support)
                consequent = set([occurences[0]])
                antecendent = set([occurences[1]])
                DetermineIfRule(antecendent, consequent, support)
    return rules


ALPHABETSIZE = 400  # 400 for 24 hours per day, 7 days per  week, 3 events, 366 days
def CreateRules(userId, confidenceThreshold = 0.7):
    data = GetEvents(userId)
    if len(data) > 0:
        key = MappingKey(data)
        mappedData = MapData(data, key)
        #print(mappedData)
        formattedOccurences, orderedFreq = OrderedOccurences(mappedData, OrderedFreqTable(mappedData))
        #print(formattedOccurences ,orderedFreq)
         
        tree = BuildTree(orderedFreq, formattedOccurences)
        #import time
        #start = time.time()
        itemset = GenerateFrequentItemSet(tree, orderedFreq)
        rules = FindAssociationRules(itemset, confidenceThreshold = 0.7)
        #print(time.time()-start)
        
        rules = UnmapRules(rules, key)
        antecendents = [rule[0] for rule in rules]
        consequents = [rule[1] for rule in rules]
        confidences = [rule[2] for rule in rules]
        return (antecendents, consequents, confidences)
    else:
        return ([], [], []) #Empty Antecdent, Consequent and Confidence
