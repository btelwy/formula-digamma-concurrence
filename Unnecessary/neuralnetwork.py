import torch
import datasets
import math
import copy

#maybe exclude data items with no "2" in them, as those are already certain
#or choose a different input besides syllable lengths, maybe normalized text
#or choose a different label format, like 0 representing spondee and 1 diphthong
#a padding token might be needed

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

randomSeed = 1234
torch.manual_seed(randomSeed)

dataset = datasets.load_dataset("csv", data_files="IliadAllCSV\\IliadCombined.csv", split="train")

trainValTest = dataset.train_test_split(test_size=0.2)
valTest = trainValTest['test'].train_test_split(test_size=0.5)

trainData = trainValTest["train"]
valData = valTest["train"]
testData = valTest["test"]

trainData.shuffle(seed=randomSeed)

print(trainData)
print(valData)
print(testData)


padToken = 3


def baseAccuracy(data):
    correctCount = 0
    syllableCorrectCount = 0
    numSyllables = 0
    mismatchCount = 0

    for item in data:
        if item["guessed"] == item["scanned"]:
            correctCount += 1
        
        guessed = str(item["guessed"])
        scanned = str(item["scanned"])

        numSyllables += len(guessed)
        if (len(guessed) == len(scanned)):
            for i in range(len(guessed)):
                if guessed[i] == scanned[i]:
                    syllableCorrectCount += 1
        else:
            mismatchCount += 1

    
    print(f"Base accuracy (over lines): {correctCount / len(data)}")
    print(f"Base accuracy (over syllables): {syllableCorrectCount / numSyllables}")
    print(f"{mismatchCount} lines have different numbers of syllables")


baseAccuracy(dataset)


def preprocess(example):
    #convert the single int in each data item to a tensor of its digits
    padToken = 3
    maxSyllables = 17 #the case where there are five dactyls + trochee/spondee
    
    example["guessed"] = torch.Tensor([int(x) for x in str(example["guessed"])])

    while (len(example["guessed"]) < maxSyllables):
        example["guessed"] = torch.cat([example["guessed"], torch.zeros(1)])
        example["guessed"][-1] = padToken

    example["scanned"] = torch.Tensor([int(x) for x in str(example["scanned"])])

    while (len(example["scanned"]) < maxSyllables):
        example["scanned"] = torch.cat([example["scanned"], torch.zeros(1)])
        example["scanned"][-1] = padToken

    return example


trainData = trainData.map(preprocess)
testData = testData.map(preprocess)
valData = valData.map(preprocess)

trainData.set_format("torch")
testData.set_format("torch")
valData.set_format("torch")


vocab = [0, 1, 2, 3]

#contains all the recorded scansion configurations in the training data
labelList = [item for item in trainData["scanned"]]

for i in range(len(labelList) - 1):
    indices = []

    for j in range(len(labelList)):
        #make sure i and j are never equal
        if j == i:
            j += 1

        if torch.equal(labelList[i], labelList[j]):
            indices.append(j)

    for k in range(len(indices)):
        labelList[indices[k]] = torch.zeros(1)

#remove duplicate configurations
labels = []

for i in range(len(labelList)):
    if not torch.equal(labelList[i], torch.zeros(1)):
        labels.append(labelList[i])

def majorityClass(trainData, testData):
    
    maxCount = 0
    maxIndex = 0

    for i in range (len(trainData["scanned"])):
        count = 0
        tensor = trainData["scanned"][i]

        for j in range (len(trainData["scanned"])):
            if torch.equal(trainData["scanned"][j], tensor):
                count += 1
        
        if count > maxCount:
            maxCount = count
            maxIndex = i
            
    mostCommon = trainData["scanned"][maxIndex]

    correctCount = 0
    trainAccuracy = 0
    testAccuracy = 0

    for item in trainData["scanned"]:
        if torch.equal(mostCommon, item):
            correctCount += 1
    
    trainAccuracy = correctCount / len(trainData)
    correctCount = 0

    for item in testData["scanned"]:
        if torch.equal(mostCommon, item):
            correctCount += 1

    testAccuracy = correctCount / len(testData)
    
    print("Train accuracy is " + str(trainAccuracy) + "\n" +
          "Test accuracy is " + str(testAccuracy))


#majorityClass(trainData, testData)


class MultiLayerPerceptron(torch.nn.Module):
    def __init__ (self, vocab, labels, pad_index, hidden_size=128): 
        super().__init__()
        self.pad_index = pad_index
        self.hidden_size = hidden_size
        # Keep the vocabulary sizes available
        self.N = len(labels) # num_classes
        self.V = len(vocab)  # vocab_size
        # Specify cross-entropy loss for optimization
        self.criterion = torch.nn.CrossEntropyLoss()
        # TODO: Create and initialize neural modules
        self.firstLayer = torch.nn.Embedding(self.V, hidden_size, pad_index)
        self.sigmoid = torch.nn.Sigmoid()
        self.secondLayer = torch.nn.Linear(hidden_size, self.N)

    def forward(self, item):
        # TODO: Calculate the logits for the `text_batch`, 
        #       returning a tensor of size batch_size x num_labels
        tensor = item["guessed"].type(torch.int64)
        return self.secondLayer(self.sigmoid(self.firstLayer(tensor)))
    
    def train_all(self, trainData, valData, epochs=8, learning_rate=3e-3):
        # Switch the module to training mode
        self.train()
        # Use Adam to optimize the parameters
        optim = torch.optim.Adam(self.parameters(), lr=learning_rate)
        best_validation_accuracy = -math.inf
        best_model = None
        # Run the optimization for multiple epochs
        for epoch in range(epochs):
            c_num = 0
            total = 0
            running_loss = 0.0
            for item in trainData:
                # TODO: set labels, compute logits (Ux in this model), 
                #       loss, and update parameters
                #very similar to logistic regression implementation
        
                optim.zero_grad()
                    
                labels = item["scanned"].type(torch.long)
                logits = self.forward(item)
                loss = self.criterion(logits, labels)

                #take a step in the opposite direction of the loss function's gradient
                loss.backward()
                    
                optim.step()
                    
                # Prepare to compute the accuracy
                predictions = torch.argmax(logits, dim=1)
                total += predictions.size(0)
                c_num += (predictions == labels).float().sum().item()        
                running_loss += loss.item() * predictions.size(0)

            # Evaluate and track improvements on the validation dataset
            validation_accuracy = self.evaluate(valData)
            if validation_accuracy > best_validation_accuracy:
                best_validation_accuracy = validation_accuracy
                self.best_model = copy.deepcopy(self.state_dict())

    def evaluate(self, data):
        # TODO: Compute accuracy
        #activate the model's evaluation mode
        self.eval()
        
        #the rest of the code is repeated from the logistic regression implementation
        c_num = 0
        count = 0
        
        for item in data:
            #as before in the train_all method
            labels = item["scanned"]
            logits = self.forward(item)
            predictions = torch.argmax(logits, dim=1)
            count += predictions.size(0)
            
            booleanTensor = (labels == predictions)
            c_num += booleanTensor.float().sum().item()
        
        print("Correct: ")
        print(labels.type(torch.long))
        print("Prediction: ")
        print(predictions)
        print("")

        return c_num / count
    

# Instantiate classifier and run it
model = MultiLayerPerceptron(vocab, labels, padToken, hidden_size=128).to(device) 
model.train_all(trainData, valData)
model.load_state_dict(model.best_model)
test_accuracy = model.evaluate(testData)
print (f'Test accuracy (over syllables) with neural network: {test_accuracy:.4f}')