---
alwaysApply: false
---
# 开发流程标准化要求书
完成一次完整开发有如下要求：
## 1.总体要求
从用户的角度思考功能设计；
从技术的角度思考功能实现；
从项目管理的角度思考项目进度；
从质量的角度思考代码质量；
一切按照用户的需求进行开发。
## 2.总体流程
接收到需求→分析任务→将任务拆分成为多个子任务→根据子任务进行模块化功能设计→撰写Plan.md记录大任务和子任务进度，记录开发流程→进行开发→全栈测试→撰写Reporter.md记录测试结果，报告开发进度和重大抉择→更新README.md记录项目介绍，更新项目进度，记录项目成员，记录项目依赖，记录项目版本，记录项目状态→提交代码到版本控制仓库→将仓库推送到远程仓库
## 3.版本控制相关问题
### 3.1提交信息规则：
feat: 新增功能
doc: 文档变更
fix: 修复bug
refactor: 代码重构
perf: 性能优化
test: 测试变更
### 3.2远程仓库
github：git@github.com:northland-studio/automidi.git
gitee：git@gitee.com:northland_studio/automidi.git
## 4.备注
README.md不要使用emoji
前端UI尽量不使用emoji