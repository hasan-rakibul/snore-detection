import os
import datetime
from omegaconf import OmegaConf
import lightning as L

from preprocessing import get_train_val_dataloader
from model import CNN1D

def main():
    config_file = "./config/config.yaml"
    config = OmegaConf.load(config_file)

    L.seed_everything(config.seed)

    if config.checkpoint:
        # use >./logs/... as logging_dir if checkpoint is provided
        print(f"\nLoading checkpoint from {config.checkpoint}")
        logging_dir = os.path.join(*config.checkpoint.split("/")[:3])
    else:
        logging_dir=os.path.join(
            config.logging_dir, 
            datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + config.expt_name
        )

    config.logging_dir = logging_dir # update logging_dir to use later

    train_loader, val_loader = get_train_val_dataloader(config)

    trainer = L.Trainer(
        max_epochs=config.train.max_epochs,
        deterministic=True,
        devices="auto",
        accelerator="auto",
        log_every_n_steps=3,
        default_root_dir=config.logging_dir,
        callbacks=[
            L.pytorch.callbacks.ModelCheckpoint(
                monitor="val_loss",
                save_top_k=1,
                mode="min"
            ),
            L.pytorch.callbacks.EarlyStopping(
                monitor="val_loss",
                patience=3,
                mode="min"
            )
        ]
    )

    if config.checkpoint:
        model = CNN1D.load_from_checkpoint(config.checkpoint)
    else:
        model = CNN1D(config)

    trainer.fit(model, train_dataloaders=train_loader, val_dataloaders=val_loader)
    trainer.validate(model, dataloaders=val_loader, verbose=True)      

if __name__ == "__main__":
    main()