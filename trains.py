"""
By xunyoyo & kesmeey
Part of code come from GitHub:
https://github.com/ziduzidu/CSDTI
"""

import logging
import math
import datetime

import torch.nn as nn
import torch.optim as optim
from sklearn.metrics import r2_score
from torch.utils.data import random_split
from torch_geometric.data import DataLoader

from model import MYMODEL
from smiles2topology import *


def save_model_dict(model, model_dir, msg):
    model_path = os.path.join(model_dir, msg + '.pt')
    torch.save(model.state_dict(), model_path)
    print("model has been saved to %s." % model_path)

foldnum=0;
MyOwnDataset.cnt1 = 0;  # 几号就是几号的数据
MyOwnDataset.num2 = 1  # 偶数就是test，否则就是train
def main():
    minnLoss=1000000;
    Ansmsg="";
    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = os.path.join('log', f"{current_time}-model.log")

    logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s')
    logging.info('Training started')

    params = dict(
        data_root="Datasets",
        save_dir="save",
        dataset="fold",
        save_model=False,
        lr=0.0005202938443000005,
        batch_size=40,
        is_using_trained_data=False,
        model_name="Epoch 1-643, Train Loss_ 1.0191, Val Loss_ 1.0195, Train R2_ 0.7854, Val R2_ 0.7982.pt"
    )


    save_dir = params.get("save_dir")
    save_model = params.get("save_model")
    DATASET = params.get("dataset")
    data_root = params.get("data_root")
    fpath = os.path.join(data_root, DATASET)

    full_dataset = MyOwnDataset(fpath, train=True)
    test_dataset1 = MyOwnDataset(os.path.join(data_root, "fold"), train=True)
    test_dataset2 = MyOwnDataset(os.path.join(data_root, "fold"), train=True)


    train_size = int(0.9 * len(full_dataset))
    val_size = len(full_dataset) - train_size

    train_set, val_set = random_split(full_dataset, [train_size, val_size])

    train_loader = DataLoader(train_set, batch_size=64, shuffle=True, num_workers=1)
    val_loader = DataLoader(val_set, batch_size=64, shuffle=True, num_workers=1)
    test1_loader = DataLoader(test_dataset1, batch_size=64, shuffle=True, num_workers=1)
    test2_loader = DataLoader(test_dataset2, batch_size=64, shuffle=True, num_workers=1)

    device = torch.device('cuda:0')

    model = MYMODEL(92, 98, 0.30467697373969527, 4, 16).to(device)

    if params.get('is_using_trained_data'):
        model.load_state_dict(torch.load(os.path.join(save_dir, params.get("model_name"))))

    epochs = 6000
    steps_per_epoch = 15
    num_iter = math.ceil((epochs * steps_per_epoch) / len(train_loader))

    optimizer = optim.Adam(model.parameters(), lr=params.get("lr"))
    criterion = nn.MSELoss()

    best_val_r2 = -float('inf')
    epochs_no_improve = 0
    early_stop_epoch = 300

    numcnt=100;#记数，100没更新就break

    for epoch in range(num_iter):
        numcnt-=1;
        if(numcnt==0):
            break
        model.train()
        train_loss = 0.0
        train_preds = []
        train_targets = []

        for data in train_loader:

            data = data.to(device)
            pred = model(data)
            loss = criterion(pred.view(-1), data.y.view(-1))

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * data.num_graphs
            train_preds.extend(pred.view(-1).detach().cpu().numpy())
            train_targets.extend(data.y.view(-1).detach().cpu().numpy())

        train_r2 = r2_score(train_targets, train_preds)

        model.eval()
        val_loss = 0.0
        val_preds = []
        val_targets = []

        with torch.no_grad():
            for data in val_loader:
                data = data.to(device)
                pred = model(data)
                loss = criterion(pred.view(-1), data.y.view(-1))

                val_loss += loss.item() * data.num_graphs
                val_preds.extend(pred.view(-1).detach().cpu().numpy())
                val_targets.extend(data.y.view(-1).detach().cpu().numpy())

        val_r2 = r2_score(val_targets, val_preds)

        model.eval()
        test1_loss = 0.0
        test1_preds = []
        test1_targets = []

        with torch.no_grad():
            for data in test1_loader:
                data = data.to(device)
                pred = model(data)
                loss = criterion(pred.view(-1), data.y.view(-1))

                test1_loss += loss.item() * data.num_graphs
                test1_preds.extend(pred.view(-1).detach().cpu().numpy())
                test1_targets.extend(data.y.view(-1).detach().cpu().numpy())

        test1_r2 = r2_score(test1_targets, test1_preds)

        model.eval()
        test2_loss = 0.0
        test2_preds = []
        test2_targets = []

        with torch.no_grad():
            for data in test2_loader:
                data = data.to(device)
                pred = model(data)
                loss = criterion(pred.view(-1), data.y.view(-1))

                test2_loss += loss.item() * data.num_graphs
                test2_preds.extend(pred.view(-1).detach().cpu().numpy())
                test2_targets.extend(data.y.view(-1).detach().cpu().numpy())

        test2_r2 = r2_score(test2_targets, test2_preds)

        train_loss = math.sqrt(train_loss / len(train_loader.dataset))
        val_loss = math.sqrt(val_loss / len(val_loader.dataset))
        test1_loss = math.sqrt(test1_loss / len(test1_loader.dataset))
        test2_loss = math.sqrt(test2_loss / len(test2_loader.dataset))
        msg = (f"fold{foldnum},Epoch {epoch + 1}-{num_iter}, "
               f"Train Loss_ {train_loss:.4f}, Val Loss_ {val_loss:.4f}, "
               f"Test1 Loss_ {test1_loss:.4f}, Test2 Loss_ {test2_loss:.4f}, "
               f"Train R2_ {train_r2:.4f}, Val R2_ {val_r2:.4f}, "
               f"Test1 R2_ {test1_r2:.4f}, Test2 R2_ {test2_r2:.4f}")
        if(val_loss<minnLoss):
            numcnt=100;
            minnLoss=val_loss
            Ansmsg=msg;
        logging.info(msg)
        print(msg)

        if save_model:
            save_model_dict(model, save_dir, msg)
            msg = os.path.join(save_dir, msg + '.pt')
            logging.info(f"model has been saved to save {msg}")

        if val_r2 > best_val_r2:
            best_val_r2 = val_r2
            epochs_no_improve = 0

        else:
            epochs_no_improve += 1

        if epochs_no_improve >= early_stop_epoch:
            logging.info(f"Early stopping triggered after {early_stop_epoch} epochs without improvement.")
            print(f"Early stopping triggered after {early_stop_epoch} epochs without improvement.")
            break


if __name__ == '__main__':

    log_dir = 'log'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_dir = 'save'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_dir = 'Maxn'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    for i in range(10):
        foldnum=i;
        MyOwnDataset.cnt1=i
        main()