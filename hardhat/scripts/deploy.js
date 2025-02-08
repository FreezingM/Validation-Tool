const hre = require("hardhat");  
const { ethers } = require("hardhat");  

async function main() {  
  try {  
    // 获取合约工厂  
    const HelloWorld = await hre.ethers.getContractFactory("HelloWorld");  
    
    // 部署合约，传入初始消息  
    const helloWorld = await HelloWorld.deploy("Hello, Blockchain World!");  
    
    // 等待部署完成  
    await helloWorld.waitForDeployment();  
    
    console.log("HelloWorld deployed to:", helloWorld.address);  
    
    // 获取当前消息  
    const message = await helloWorld.getMessage();  
    console.log("Initial message:", message); 
    
    // 设置新消息  
    const tx = await helloWorld.setMessage("Hello, Updated World!");  
    await tx.wait();  
    
    // 获取更新后的消息  
    const newMessage = await helloWorld.getMessage();  
    console.log("Updated message:", newMessage);  
    
  } catch (error) {  
    console.error("部署过程中出现错误:", error);  
    process.exit(1);  
  }  
}  

main()  
  .then(() => process.exit(0))  
  .catch((error) => {  
    console.error(error);  
    process.exit(1);  
  });