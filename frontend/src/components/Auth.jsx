import { useState } from "react"
import { supabase } from "../api/supabase"

// Auth component
export default function Auth() {
  const [email, setEmail] = useState("")
  const [message, setMessage] = useState("")

  const handleSubmit = async (event) => {
    event.preventDefault()

    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: window.location.origin,
      },
    })

    if (error) {
      setMessage(error.message)
      return
    }

    setMessage("Check your email for the sign-in link.")
  }

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        placeholder="Email address"
        required
      />

      <button type="submit">
        Send sign-in link
      </button>

      {message && <p>{message}</p>}
    </form>
  )
}