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
  email: string
  phone: string
  address: string
  city: string
  country: string
}

const initialState: FormState = {
  username: "",
  password: "",
  email: "",
  phone: "",
  address: "",
  city: "",
  country: "",
}

export function AuthPage({ mode }: Props) {
  const [form, setForm] = useState<FormState>(initialState)
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
    if (mode === "login") {
      loginMutation.mutate()
      return
    }
    registerMutation.mutate()
  }

  return (
    <section className="panel narrow-panel">
      <h1>{mode === "login" ? "Customer Login" : "Customer Register"}</h1>
      <div className="form-grid">
        <label>
          Username
          <input
            className="field"
            value={form.username}
            onChange={(event) => setForm((prev) => ({ ...prev, username: event.target.value }))}
          />
        </label>

        <label>
          Password
          <input
            className="field"
            type="password"
            value={form.password}
            onChange={(event) => setForm((prev) => ({ ...prev, password: event.target.value }))}
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

            <label>
              Phone
              <input
                className="field"
                value={form.phone}
                onChange={(event) => setForm((prev) => ({ ...prev, phone: event.target.value }))}
              />
            </label>

            <label>
              Address
              <input
                className="field"
                value={form.address}
                onChange={(event) => setForm((prev) => ({ ...prev, address: event.target.value }))}
              />
            </label>

            <label>
              City
              <input
                className="field"
                value={form.city}
                onChange={(event) => setForm((prev) => ({ ...prev, city: event.target.value }))}
              />
            </label>

            <label>
              Country
              <input
                className="field"
                value={form.country}
                onChange={(event) => setForm((prev) => ({ ...prev, country: event.target.value }))}
              />
            </label>
          </>
        ) : null}
      </div>

      <div className="row-actions">
        <button
          className="primary-button"
          onClick={submit}
          disabled={loginMutation.isPending || registerMutation.isPending}
        >
          {mode === "login" ? "Login" : "Register"}
        </button>

        {mode === "login" ? <Link to="/auth/register">Need account? Register</Link> : null}
        {mode === "register" ? <Link to="/auth/login">Already have account? Login</Link> : null}
      </div>

      {loginMutation.isError ? <p className="error-text">{getApiErrorMessage(loginMutation.error)}</p> : null}
      {registerMutation.isError ? <p className="error-text">{getApiErrorMessage(registerMutation.error)}</p> : null}
      {registerMutation.isSuccess ? <p className="success-text">Registered. Redirecting to login...</p> : null}
    </section>
  )
}