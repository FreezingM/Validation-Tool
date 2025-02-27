document.addEventListener('DOMContentLoaded', function() {
    // 获取所有需要的DOM元素
    const generateReportBtn = document.getElementById('generateReport');
    const reportResult = document.getElementById('reportResult');
    const reportContent = document.getElementById('reportContent');
    
    // 监听验证类型的变化，控制抽样率输入框的显示/隐藏
    document.querySelectorAll('input[name="validationType"]').forEach(radio => {
        radio.addEventListener('change', function() {
            const sampleRateGroup = document.getElementById('sampleRateGroup');
            sampleRateGroup.style.display = this.value === 'sample' ? 'block' : 'none';
        });
    });

    // 点击生成报告按钮时的处理
    generateReportBtn.addEventListener('click', async function() {
        // 收集表单数据
        const formData = {
            network_type: document.getElementById('sourceChain').value.toLowerCase(), // 转换为小写以匹配后端
            start_block: document.getElementById('sourceStartBlock').value,
            end_block: document.getElementById('sourceEndBlock').value,
            // 如果需要目标链的数据也可以添加
            target_network_type: document.getElementById('targetChain').value.toLowerCase(),
            target_start_block: document.getElementById('targetStartBlock').value,
            target_end_block: document.getElementById('targetEndBlock').value
        };

        // 表单验证
        if (!validateForm(formData)) {
            return;
        }

        try {
            // 清空之前的日志
            document.getElementById('logContent').innerHTML = '';
            
            // 发送请求到后端
            const response = await fetch('/api/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            // 获取响应的数据流
            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const {value, done} = await reader.read();
                if (done) break;
                
                const text = decoder.decode(value);
                // 处理接收到的数据
                try {
                    // 尝试解析为JSON（最终报告）
                    const jsonData = JSON.parse(text);
                    handleFinalReport(jsonData);
                } catch (e) {
                    // 如果不是JSON，则作为日志处理
                    handleLog(text);
                }
            }

        } catch (error) {
            handleLog('错误：' + error.message);
        }
    });

    // 表单验证函数
    function validateForm(data) {
        if (!data.sourceChain) {
            alert('请选择源链');
            return false;
        }
        if (!data.targetChain) {
            alert('请选择目标链');
            return false;
        }
        if (!data.sourceStartBlock || !data.sourceEndBlock) {
            alert('请输入源链区块范围');
            return false;
        }
        if (!data.targetStartBlock || !data.targetEndBlock) {
            alert('请输入目标链区块范围');
            return false;
        }
        if (parseInt(data.sourceStartBlock) > parseInt(data.sourceEndBlock)) {
            alert('源链起始区块不能大于结束区块');
            return false;
        }
        if (parseInt(data.targetStartBlock) > parseInt(data.targetEndBlock)) {
            alert('目标链起始区块不能大于结束区块');
            return false;
        }
        if (data.validationType === 'sample' && 
            (data.sampleRate < 1 || data.sampleRate > 100)) {
            alert('抽样率必须在1-100之间');
            return false;
        }
        return true;
    }

    // 输出报告结果
    function displayReport(data) {
        reportResult.style.display = 'block';
        reportContent.innerHTML = `
            <div class="report-item">
                <p>验证状态: ${data.status}</p>
                <p>验证区块数: ${data.totalBlocks}</p>
                <p>匹配区块数: ${data.matchedBlocks}</p>
                <p>不匹配区块数: ${data.unmatchedBlocks}</p>
                <p>验证完成时间: ${new Date().toLocaleString()}</p>
                ${data.errorBlock ? `
                    <p>异常区块: ${data.errorBlock}</p>
                    <p>异常内容: ${data.errorContent}</p>
                ` : ''}
            </div>
        `;
    }

    // 导出CSV功能
    document.getElementById('exportCSV').addEventListener('click', function() {
        // 此功能未写
        alert('导出CSV功能待实现');
    });

    // 添加一个日志显示区域
    function addLogDisplay() {
        const logSection = `
            <div class="form-section" id="logSection">
                <h2>验证日志</h2>
                <div id="logContent" class="log-content"></div>
            </div>
        `;
        
        // 将日志区域插入到表单后面
        document.querySelector('.report-result').insertAdjacentHTML('beforebegin', logSection);
    }

    // 处理日志信息
    function handleLog(logMessage) {
        const logContent = document.getElementById('logContent');
        // 添加新的日志条目
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        
        // 根据日志类型添加不同的样式
        if (logMessage.includes('错误') || logMessage.includes('有误')) {
            logEntry.classList.add('error-log');
        }
        
        logEntry.textContent = logMessage;
        logContent.appendChild(logEntry);
        // 自动滚动到最新的日志
        logContent.scrollTop = logContent.scrollHeight;
    }

    // 处理最终报告
    function handleFinalReport(report) {
        const reportContent = document.getElementById('reportContent');
        
        // 显示验证结果
        reportContent.innerHTML = `
            <div class="report-item">
                <p>验证状态: ${report.hasError ? '部分错误' : '验证通过'}</p>
                <p>验证区块数: ${report.totalBlocks || 0}</p>
                <p>匹配区块数: ${report.matchedBlocks || 0}</p>
                <p>不匹配区块数: ${report.unmatchedBlocks || 0}</p>
                ${report.errorBlock ? `<p>异常区块: ${report.errorBlock}</p>` : ''}
                ${report.errorContent ? `<p>异常内容: ${report.errorContent}</p>` : ''}
                <p>验证完成时间: ${new Date().toLocaleString()}</p>
            </div>
        `;
    }

    // 在页面加载时添加日志显示区域
    addLogDisplay();
}); 