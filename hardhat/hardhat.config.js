require("@nomicfoundation/hardhat-toolbox");

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: "0.8.19",
  networks: {  
    ganache: {  
      url: "http://127.0.0.1:7545",  
      accounts: ['0x7f2cb271ef806cf207d05f12797a56e19a9e923b3f3469e79b080bf562fcefd6']  
    }  
  }  
};
