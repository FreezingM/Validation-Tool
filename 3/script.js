document.addEventListener('DOMContentLoaded', function() {
    // 获取按钮和日志区域元素
    const extractButton = document.getElementById('extractData');
    const validateButton = document.getElementById('validateData');
    const logContent = document.getElementById('logContent');

    // 添加日志的函数
    function addLog(message) {
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        logEntry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
        logContent.appendChild(logEntry);
        // 自动滚动到最新日志
        logContent.scrollTop = logContent.scrollHeight;
    }

    // 数据获取功能
    async function handleExtract() {
        try {
            extractButton.disabled = true;
            extractButton.textContent = '数据获取中...';

            const formData = {
                network_type: document.getElementById('sourceChain').value.toLowerCase(),
                start_block: document.getElementById('sourceStartBlock').value,
                end_block: document.getElementById('sourceEndBlock').value,
                target_network_type: document.getElementById('targetChain').value.toLowerCase(),
                target_start_block: document.getElementById('targetStartBlock').value,
                target_end_block: document.getElementById('targetEndBlock').value
            };

            addLog('开始获取数据...');

            const response = await fetch('http://localhost:5000/api/extract', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();
            
            if (data.status === 'success') {
                addLog('✅ ' + data.message);
                
                // 显示源链数据
                addLog('\n源链数据:');
                addLog(`网络类型: ${data.source_chain.network_type}`);
                addLog(`区块范围: ${data.source_chain.start_block} - ${data.source_chain.end_block}`);

                // 显示目标链数据
                addLog('\n目标链数据:');
                addLog(`网络类型: ${data.target_chain.network_type}`);
                addLog(`区块范围: ${data.target_chain.start_block} - ${data.target_chain.end_block}`);

            } else {
                addLog('❌ 数据获取失败: ' + data.message);
            }

        } catch (error) {
            addLog('❌ 错误: ' + error.message);
            console.error('Extract error:', error);
        } finally {
            extractButton.disabled = false;
            extractButton.textContent = '数据获取';
        }
    }

    // 数据校验功能
    async function handleValidate() {
        try {
            validateButton.disabled = true;
            validateButton.textContent = '校验中...';

            const formData = {
                network_type: document.getElementById('sourceChain').value.toLowerCase(),
                start_block: document.getElementById('sourceStartBlock').value,
                end_block: document.getElementById('sourceEndBlock').value,
                target_network_type: document.getElementById('targetChain').value.toLowerCase(),
                target_start_block: document.getElementById('targetStartBlock').value,
                target_end_block: document.getElementById('targetEndBlock').value
            };

            addLog('开始数据校验...');
            // 显示发送的验证请求
            addLog('验证请求已发送:');
            addLog(JSON.stringify(formData, null, 2));

            const response = await fetch('http://localhost:5000/api/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();
            
            if (data.status === 'success') {
                addLog('✅ ' + data.message);
                // 显示服务器响应数据
                addLog('服务器响应:');
                addLog(JSON.stringify({
                    source_chain: data.source_chain,
                    target_chain: data.target_chain
                }, null, 2));
            } else {
                addLog('❌ 校验失败: ' + data.message);
            }

        } catch (error) {
            addLog('❌ 错误: ' + error.message);
            console.error('Validation error:', error);
        } finally {
            validateButton.disabled = false;
            validateButton.textContent = '数据校验';
        }
    }

    // 添加按钮点击事件监听器
    extractButton.addEventListener('click', handleExtract);
    validateButton.addEventListener('click', handleValidate);
}); 