"""
Train MNIST FCNN matching VNN-COMP 2021 mnistfc benchmark (2-layer variant).
Architecture: 784 → 256 → 256 → 10 (pure ReLU, standard training).
This is the standard model used in VNN-COMP 2020 and 2021 mnistfc benchmarks.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms
import os

class FCNN_VNNCOMP_2Layer(nn.Module):
    """2-layer FC network matching VNN-COMP mnistfc 2-layer architecture."""
    def __init__(self):
        super().__init__()
        self.flatten = nn.Flatten()
        self.fc1 = nn.Linear(28 * 28, 256)
        self.relu1 = nn.ReLU()
        self.fc2 = nn.Linear(256, 256)
        self.relu2 = nn.ReLU()
        self.fc3 = nn.Linear(256, 10)

    def forward(self, x):
        x = self.flatten(x)
        x = self.relu1(self.fc1(x))
        x = self.relu2(self.fc2(x))
        x = self.fc3(x)
        return x


def train():
    transform = transforms.Compose([transforms.ToTensor()])
    train_dataset = datasets.MNIST(root='./data', train=True, download=True, transform=transform)
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=128, shuffle=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    model = FCNN_VNNCOMP_2Layer().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    epochs = 5
    model.train()
    for epoch in range(epochs):
        total_loss = 0
        correct = 0
        for batch_idx, (data, target) in enumerate(train_loader):
            data, target = data.to(device), target.to(device)
            optimizer.zero_grad()
            output = model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            pred = output.argmax(dim=1, keepdim=True)
            correct += pred.eq(target.view_as(pred)).sum().item()
        acc = 100. * correct / len(train_loader.dataset)
        print(f"Epoch {epoch+1}/{epochs} | Loss: {total_loss/len(train_loader):.4f} | Acc: {acc:.2f}%")

    # Save
    os.makedirs("saved_models", exist_ok=True)
    torch.save(model.state_dict(), "saved_models/mnist_fcnn_vnncomp_2layer.pth")
    print("Saved PyTorch weights -> saved_models/mnist_fcnn_vnncomp_2layer.pth")

    model.eval()
    dummy_input = torch.randn(1, 1, 28, 28).to(device)
    torch.onnx.export(model, dummy_input, "saved_models/mnist_fcnn_vnncomp_2layer.onnx",
                      export_params=True, opset_version=11,
                      do_constant_folding=True,
                      input_names=['input'], output_names=['output'])
    print("Exported ONNX -> saved_models/mnist_fcnn_vnncomp_2layer.onnx")

    # Quick test accuracy
    test_dataset = datasets.MNIST(root='./data', train=False, download=True, transform=transform)
    test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=1000, shuffle=False)
    correct = 0
    with torch.no_grad():
        for data, target in test_loader:
            data, target = data.to(device), target.to(device)
            output = model(data)
            pred = output.argmax(dim=1)
            correct += pred.eq(target).sum().item()
    test_acc = 100. * correct / len(test_dataset)
    print(f"Test Accuracy: {test_acc:.2f}% ({correct}/{len(test_dataset)})")


if __name__ == '__main__':
    train()
