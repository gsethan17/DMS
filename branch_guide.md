# GIT Branch Guide
### Github repository에서 특정 branch만 clone하는 방법
```
$ git clone –b <branchName> --single-branch https://github.com/gsethan17/DMS.git
    ## <branchName>: Audio, CAN, HMI, Sensor, Video 중 1개 선택
    ## DMS 폴더가 clone됨
$ cd DMS
$ git branch  
$ cd <branchName>
```
### 작업 진행 후 해당 branch의 remote repository로 push하는 방법
```
$ git add <fileName> ## 모든 폴더 add 시: $ git add .
$ git commit –m “commit message…”
$ git push origin <branchName>
```