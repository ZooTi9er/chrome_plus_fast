import numpy as np

class NeuralNetwork:
    def __init__(self, input_size, hidden_size, output_size):
        self.weights1 = np.random.randn(input_size, hidden_size)
        self.weights2 = np.random.randn(hidden_size, output_size)

    def forward(self, X):
        self.hidden = np.dot(X, self.weights1)
        self.hidden_activated = self.sigmoid(self.hidden)
        self.output = np.dot(self.hidden_activated, self.weights2)
        return self.output

    def sigmoid(self, x):
        return 1 / (1 + np.exp(-x))

# 示例用法
if __name__ == '__main__':
    nn = NeuralNetwork(2, 4, 1)
    X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
    print(nn.forward(X))