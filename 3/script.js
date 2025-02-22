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
            sourceChain: document.getElementById('sourceChain').value,
            targetChain: document.getElementById('targetChain').value,
            startBlock: document.getElementById('startBlock').value,
            endBlock: document.getElementById('endBlock').value,
            validationType: document.querySelector('input[name="validationType"]:checked').value,
            sampleRate: document.getElementById('sampleRate').value
        };

        // 表单验证
        if (!validateForm(formData)) {
            return;
        }

        try {
            // 显示加载状态
            generateReportBtn.disabled = true;
            generateReportBtn.textContent = '生成报告中...';

            // 发送API请求
            //json格式发送
            const response = await fetch('http://127.0.0.1:5000', {//在这里修改API的地址
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (response.ok) {
                // 显示报告结果
                displayReport(data);
            } else {
                throw new Error(data.message || '生成报告失败');
            }

        } catch (error) {
            alert('错误：' + error.message);
        } finally {
            // 恢复按钮状态
            generateReportBtn.disabled = false;
            generateReportBtn.textContent = '生成报告';
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
        if (!data.startBlock) {
            alert('请输入起始区块');
            return false;
        }
        if (!data.endBlock) {
            alert('请输入结束区块');
            return false;
        }
        if (parseInt(data.startBlock) > parseInt(data.endBlock)) {
            alert('起始区块不能大于结束区块');
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
}); 