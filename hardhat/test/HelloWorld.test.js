const { expect } = require("chai");  
const { ethers } = require("hardhat");  

describe("HelloWorld", function () {  
  let helloWorld;  
  
  beforeEach(async function () {  
    // 正确的部署方式  
    const HelloWorld = await ethers.getContractFactory("HelloWorld");  
    helloWorld = await HelloWorld.deploy("Hello, Test World!");  
    await helloWorld.waitForDeployment();  
  });  

  it("Should return the correct initial message", async function () {  
    expect(await helloWorld.getMessage()).to.equal("Hello, Test World!");  
  });  

  it("Should update the message correctly", async function () {  
    await helloWorld.setMessage("New Message");  
    expect(await helloWorld.getMessage()).to.equal("New Message");  
  });  
});