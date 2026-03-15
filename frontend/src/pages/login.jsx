import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Login() {

  const [username,setUsername] = useState("");
  const [password,setPassword] = useState("");

  const navigate = useNavigate();

  async function login(){

    const formData = new URLSearchParams();
    formData.append("username",username);
    formData.append("password",password);

    const res = await fetch("http://localhost:8000/api/login",{
      method:"POST",
      headers:{
        "Content-Type":"application/x-www-form-urlencoded"
      },
      body:formData
    });

    const data = await res.json();

    if(data.access_token){

      localStorage.setItem("nova_token",data.access_token);

      navigate("/dashboard");
    }
    else{
      alert("Login failed");
    }
  }

  return(

    <div style={{padding:40}}>

      <h1>NOVA LOGIN</h1>

      <input
      placeholder="username"
      onChange={(e)=>setUsername(e.target.value)}
      />

      <br/><br/>

      <input
      type="password"
      placeholder="password"
      onChange={(e)=>setPassword(e.target.value)}
      />

      <br/><br/>

      <button onClick={login}>Login</button>

    </div>
  )
}