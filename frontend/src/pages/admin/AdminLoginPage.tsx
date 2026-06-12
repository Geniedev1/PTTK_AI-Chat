import { useMutation } from "@tanstack/react-query"
import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { staffApi } from "../../shared/api/services"
import { useSessionStore } from "../../shared/stores/sessionStore"
import { getApiErrorMessage } from "../../shared/utils/apiError"

export function AdminLoginPage() {
  const navigate = useNavigate()
  const setStaffAuth = useSessionStore((state) => state.setStaffAuth)
  const [form, setForm] = useState({ username: "", password: "" })

  const loginMutation = useMutation({
    mutationFn: () => staffApi.login({ username: form.username.trim(), password: form.password }),
    onSuccess: (data) => {
      setStaffAuth({
        token: data.token,
        staffId: data.staff.id,
        staffName: data.staff.name,
        staffRoles: data.staff.roles,
      })
      void navigate(data.staff.roles.includes("admin") ? "/admin" : "/shipper")
    },
  })

  return (
    <section className="panel auth-panel">
      <h1>Staff Login</h1>
      <form
        className="form-grid"
        onSubmit={(event) => {
          event.preventDefault()
          loginMutation.mutate()
        }}
      >
        <label>
          Username
          <input
            className="field"
            value={form.username}
            onChange={(event) => setForm((current) => ({ ...current, username: event.target.value }))}
            autoComplete="username"
          />
        </label>
        <label>
          Password
          <input
            className="field"
            type="password"
            value={form.password}
            onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
            autoComplete="current-password"
          />
        </label>
        <button className="primary-button" disabled={loginMutation.isPending}>
          Sign In
        </button>
      </form>
      {loginMutation.isError ? <p className="error-text">{getApiErrorMessage(loginMutation.error)}</p> : null}
    </section>
  )
}
