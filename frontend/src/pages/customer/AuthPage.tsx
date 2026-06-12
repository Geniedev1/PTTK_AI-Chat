import { useMutation } from "@tanstack/react-query"
import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { customerApi } from "../../shared/api/services"
import { useSessionStore } from "../../shared/stores/sessionStore"
import type { CustomerRegisterPayload } from "../../shared/types/api"
import { getApiErrorMessage } from "../../shared/utils/apiError"

type Props = {
  mode: "login" | "register"
}

type FormState = {
  username: string
  password: string
  confirmPassword: string
  email: string
  phone: string
  address: string
  city: string
  country: string
}

const initialState: FormState = {
  username: "",
  password: "",
  confirmPassword: "",
  email: "",
  phone: "",
  address: "",
  city: "",
  country: "",
}

export function AuthPage({ mode }: Props) {
  const [form, setForm] = useState<FormState>(initialState)
  const [localError, setLocalError] = useState("")
  const navigate = useNavigate()
  const setCustomerAuth = useSessionStore((state) => state.setCustomerAuth)

  const loginMutation = useMutation({
    mutationFn: () => customerApi.login({ username: form.username.trim(), password: form.password }),
    onSuccess: (data) => {
      setCustomerAuth({
        token: data.token,
        customerId: data.customer.id,
        customerUsername: data.customer.user.username,
      })
      void navigate("/products")
    },
  })

  const registerMutation = useMutation({
    mutationFn: () => {
      const payload: CustomerRegisterPayload = {
        username: form.username.trim(),
        password: form.password,
        email: form.email.trim(),
      }

      const phone = form.phone.trim()
      const address = form.address.trim()
      const city = form.city.trim()
      const country = form.country.trim()

      if (phone) {
        payload.phone = phone
      }
      if (address) {
        payload.address = address
      }
      if (city) {
        payload.city = city
      }
      if (country) {
        payload.country = country
      }

      return customerApi.register(payload)
    },
    onSuccess: () => {
      void navigate("/auth/login")
    },
  })

  const submit = () => {
    setLocalError("")
    if (mode === "login") {
      loginMutation.mutate()
      return
    }
    if (form.password !== form.confirmPassword) {
      setLocalError("Password confirmation does not match.")
      return
    }
    registerMutation.mutate()
  }

  return (
    <section className={mode === "login" ? "auth-page login-auth" : "auth-page register-auth"}>
      <div className="auth-visual" aria-hidden="true" />
      <div className="auth-panel">
        <h1>AuraShop</h1>
        <h2>{mode === "login" ? "Welcome Back" : "Create an Account"}</h2>
        <div className="auth-form">
          <label>
            Username
            <input
              className="field"
              value={form.username}
              placeholder="Username"
              onChange={(event) => setForm((prev) => ({ ...prev, username: event.target.value }))}
            />
          </label>

        {mode === "register" ? (
          <>
            <label>
              Email
              <input
                className="field"
                type="email"
                value={form.email}
                onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))}
              />
            </label>
          </>
        ) : null}

          <label>
            Password
            <input
              className="field"
              type="password"
              placeholder="Password"
              value={form.password}
              onChange={(event) => setForm((prev) => ({ ...prev, password: event.target.value }))}
            />
          </label>

        {mode === "register" ? (
          <>
            <label>
              Confirm Password
              <input
                className="field"
                type="password"
                placeholder="Confirm Password"
                value={form.confirmPassword}
                onChange={(event) => setForm((prev) => ({ ...prev, confirmPassword: event.target.value }))}
              />
            </label>
            <label>
              Phone
              <input
                className="field"
                value={form.phone}
                onChange={(event) => setForm((prev) => ({ ...prev, phone: event.target.value }))}
              />
            </label>
            <label className="auth-check">
              <input type="checkbox" />
              I agree to the <span>Terms and Conditions</span>
            </label>
            <label className="auth-check">
              <input type="checkbox" />
              Join AI Stylist Program <em>AI</em> (optional)
            </label>
          </>
        ) : null}
        </div>

      <div className="auth-actions">
        {mode === "login" ? <Link to="/auth/login">Forgot Password?</Link> : null}
        <button
          className="primary-button"
          onClick={submit}
          disabled={loginMutation.isPending || registerMutation.isPending}
        >
          {mode === "login" ? "Sign In" : "Create Account"}
        </button>
        {mode === "login" ? (
          <>
            <div className="auth-divider"><span>Or sign in with</span></div>
            <div className="social-row">
              <button>G</button>
              <button>A</button>
            </div>
            <p>
              Don't have an account? <Link to="/auth/register">Create an account</Link>
            </p>
          </>
        ) : (
          <Link className="back-login" to="/auth/login">Back to Login</Link>
        )}
      </div>

      {localError ? <p className="error-text">{localError}</p> : null}
      {loginMutation.isError ? <p className="error-text">{getApiErrorMessage(loginMutation.error)}</p> : null}
      {registerMutation.isError ? <p className="error-text">{getApiErrorMessage(registerMutation.error)}</p> : null}
      {registerMutation.isSuccess ? <p className="success-text">Registered. Redirecting to login...</p> : null}
      </div>
    </section>
  )
}
