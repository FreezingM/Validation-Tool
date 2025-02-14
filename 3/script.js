document.addEventListener('DOMContentLoaded', function() {
    // 获取元素
    const sampleValidation = document.getElementById('sampleValidation');
    const fullValidation = document.getElementById('fullValidation');
    const sampleRateGroup = document.getElementById('sampleRateGroup');
    const generateReport = document.getElementById('generateReport');
    const reportResult = document.getElementById('reportResult');
    const reportContent = document.getElementById('reportContent');
    const exportCSV = document.getElementById('exportCSV');

    // 处理抽样校验选项的显示/隐藏
    sampleValidation.addEventListener('change', function() {
        sampleRateGroup.style.display = 'block';
    });

    fullValidation.addEventListener('change', function() {
        sampleRateGroup.style.display = 'none';
    });

    // 生成报告
    generateReport.addEventListener('click', function() {
        const sourceChain = document.getElementById('sourceChain').value;
        const targetChain = document.getElementById('targetChain').value;
        const startBlock = document.getElementById('startBlock').value;
        const endBlock = document.getElementById('endBlock').value;
        const validationType = document.querySelector('input[name="validationType"]:checked').value;
        const sampleRate = document.getElementById('sampleRate').value;

        // 验证表单
        if (!sourceChain || !targetChain || !startBlock || !endBlock) {
            alert('请填写所有必要信息！');
            return;
        }

        // 生成报告内容
        const reportHTML = `
            <p><strong>验证时间：</strong> ${new Date().toLocaleString()}</p>
            <p><strong>源链：</strong> ${sourceChain}</p>
            <p><strong>目标链：</strong> ${targetChain}</p>
            <p><strong>区块范围：</strong> ${startBlock} - ${endBlock}</p>
            <p><strong>验证方式：</strong> ${validationType === 'full' ? '全量校验' : '抽样校验'}</p>
            ${validationType === 'sample' ? `<p><strong>抽样率：</strong> ${sampleRate}%</p>` : ''}
        `;

        reportContent.innerHTML = reportHTML;
        reportResult.style.display = 'block';
    });

    // 导出CSV
    exportCSV.addEventListener('click', function() {
        const sourceChain = document.getElementById('sourceChain').value;
        const targetChain = document.getElementById('targetChain').value;
        const startBlock = document.getElementById('startBlock').value;
        const endBlock = document.getElementById('endBlock').value;
        
        // 创建CSV内容
        const csvContent = `源链,目标链,起始区块,结束区块\n${sourceChain},${targetChain},${startBlock},${endBlock}`;
        
        // 创建Blob对象
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        
        // 创建下载链接
        const link = document.createElement("a");
        if (link.download !== undefined) {
            const url = URL.createObjectURL(blob);
            link.setAttribute("href", url);
            link.setAttribute("download", `验证报告_${new Date().getTime()}.csv`);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    });
}); 