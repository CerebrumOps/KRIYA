> see there is nothing like options anyhow we can give it n numbers of tools even if it have terminal tool,

  The thing is I am thinking of keeping entire Application inside the docker container itself and one click installation instead of login based container we put all files into the docker and one click
  installation, when user opens app it opens up in browser directly because the shell automation script will run the frontend and agent main harness and quicky opens up in browser. then login and use so
  here we are literally keeping the agent itself inside the contianer OS no need to change the current code.

  I mean it's done this is the first version we have which could do something atleast before we make more features lets deploy and make it a proper app


  but first of all the backend part is concerning what do you think right now we have to take the application database out of the current backend folder and make a another backend folder and put the database codes and initializations in it
  then rename the current backend folder as agent-harness, but I am thinkning is there anything else I need to include?
  













    Here is what is happening right now:

```mermaid
flowchart TD
    subgraph Central_Servers["Central Infrastructure - Shared by All Users"]
        MB["Raspberry Pi / GPU Server<br/>Model Balancer - port 8000/v1<br/>No heavy AI download on user laptop"]
        MCP["Raspberry Pi / Plant Server<br/>CompanyDB + FastMCP - port 8085<br/>Live SCADA telemetry and alarms"]
    end

    subgraph User_Laptop["Engineer's Laptop - Distributed Appliance"]
        direction TB
        LAUNCH["One-click launch: ./start.sh"]
        BROWSER["Web browser: localhost:3000"]
        CONT["kriya-workbench Docker container<br/>Ubuntu 24.04<br/>Root terminal: apt, pip, python, bash<br/>PostgreSQL app database<br/>FastAPI + Agent Orchestrator"]
        HOST_DIR["Host folder: ~/kriya-shared<br/>User files and agent reports"]

        LAUNCH --> CONT
        LAUNCH --> BROWSER
        CONT <-->|Bridge tools| HOST_DIR
        BROWSER <--> CONT
    end

    CONT -->|Tokens and JSON| MB
    CONT -->|FastMCP tool calls| MCP

    style MB fill:#10b981,color:#fff
    style MCP fill:#10b981,color:#fff
    style CONT fill:#3b82f6,color:#fff
    style HOST_DIR fill:#f59e0b,color:#000
    style Central_Servers fill:#f8fafc,stroke:#94a3b8
    style User_Laptop fill:#f8fafc,stroke:#94a3b8
```
















> /plan Hey you fool I said the client app must be inside the docker, Omg that means you gave full stuff to backend... holy shit... I said client in Docker container OS, the have
  nothing to do with the docker OS it just handles and routes the DB requests and model requests the entire agent and docker OS is with the user and the blob stoareges.

  do one thing eliminate the db calls from backend let the backend only routes to model balancer and the credentials + login and employee details part..

  we will make the conversations storage within client app that mean docker container OS. Just like how you work the AntigraviryCLI, same way this will work, so whom ever gets login the
  chats are going to be same nothing to do with it


  client app frontend and agent harness completely put that code into docker OS, then backend for login credentials otps etc etc, and remiaining two piecces wil do theit job