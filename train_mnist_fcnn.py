import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms
import os

# 1. 定义全连接神经网络 (严格遵循题目要求：FCNN + ReLU)
class FCNN_ReLU(nn.Module):
    def __init__(self):
        super(FCNN_ReLU, self).__init__()
        self.flatten = nn.Flatten()
        # 输入层 28x28=784，两个隐藏层 (256, 128)，输出层 10 (类别)
        self.fc1 = nn.Linear(28 * 28, 256)
        self.relu1 = nn.ReLU()
        self.fc2 = nn.Linear(256, 128)
        self.relu2 = nn.ReLU()
        self.fc3 = nn.Linear(128, 10)

    def forward(self, x):
        x = self.flatten(x)
        x = self.fc1(x)
        x = self.relu1(x)
        x = self.fc2(x)
        x = self.relu2(x)
        x = self.fc3(x)
        return x

def train():
    # 2. 准备数据集 (MNIST)
    transform = transforms.Compose([transforms.ToTensor()])
    
    # 自动下载并加载训练集
    train_dataset = datasets.MNIST(root='./data', train=True, download=True, transform=transform)
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=128, shuffle=True)

    # 3. 初始化模型、损失函数和优化器
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"训练使用的设备: {device}")
    
    model = FCNN_ReLU().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    # 4. 开始训练 (为了快速拿到靶标，我们只跑 5 个 Epoch)
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
        print(f"Epoch {epoch+1}/{epochs} | Loss: {total_loss/len(train_loader):.4f} | Accuracy: {acc:.2f}%")

    # 5. 保存模型 (划重点：保存为 ONNX 格式以便于验证)
    os.makedirs("saved_models", exist_ok=True)
    
    # 保存常规的 pth 权重
    torch.save(model.state_dict(), "saved_models/mnist_fcnn.pth")
    print("已保存 PyTorch 权重 -> saved_models/mnist_fcnn.pth")
    
    # 导出为 ONNX 格式 (验证工具最爱)
    model.eval()
    dummy_input = torch.randn(1, 1, 28, 28).to(device) # 模拟一张 MNIST 图片的维度
    torch.onnx.export(model, dummy_input, "saved_models/mnist_fcnn.onnx",
                      export_params=True,
                      opset_version=11,
                      do_constant_folding=True,
                      input_names=['input'],
                      output_names=['output'])
    print("已导出 ONNX 模型 -> saved_models/mnist_fcnn.onnx")

if __name__ == '__main__':
    train()