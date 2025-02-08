// SPDX-License-Identifier: MIT  
pragma solidity ^0.8.19;  

contract HelloWorld {  
    string private message;  
    
    // 事件声明  
    event MessageChanged(string newMessage);  
    
    // 构造函数  
    constructor(string memory initialMessage) {  
        message = initialMessage;  
    }  
    
    // 获取消息  
    function getMessage() public view returns (string memory) {  
        return message;  
    }  
    
    // 设置新消息  
    function setMessage(string memory newMessage) public {  
        message = newMessage;  
        emit MessageChanged(newMessage);  
    }  
}  