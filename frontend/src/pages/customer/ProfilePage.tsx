import { useMutation, useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { Link } from "react-router-dom"
import { customerApi } from "../../shared/api/services"
import { useSessionStore } from "../../shared/stores/sessionStore"
import { getApiErrorMessage } from "../../shared/utils/apiError"

type ProfileForm = {
  phone: string
  address: string
  city: string
  country: string
}

export function ProfilePage() {
  const customerToken = useSessionStore((state) => state.customerToken)
  const [draft, setDraft] = useState<Partial<ProfileForm>>({})

  const profileQuery = useQuery({
    queryKey: ["customer", "profile"],
    queryFn: customerApi.profile,
    enabled: Boolean(customerToken),
  })

  const updateMutation = useMutation({
    mutationFn: () => {
      const profile = profileQuery.data
      return customerApi.updateProfile({
        phone: (draft.phone ?? profile?.phone ?? "").trim(),
        address: (draft.address ?? profile?.address ?? "").trim(),
        city: (draft.city ?? profile?.city ?? "").trim(),
        country: (draft.country ?? profile?.country ?? "").trim(),
      })
    },
    onSuccess: () => {
      setDraft({})
    },
  })

  if (!customerToken) {
    return (
      <section className="panel narrow-panel">
        <h1>Profile</h1>
        <p>You need to login before viewing profile data.</p>
        <div className="row-actions">
          <Link to="/auth/login">Login</Link>
          <Link to="/auth/register">Register</Link>
        </div>
      </section>
    )
  }

  return (
    <section className="panel narrow-panel">
      <h1>Profile</h1>
      {profileQuery.isLoading ? <p>Loading profile...</p> : null}
      {profileQuery.isError ? <p className="error-text">{getApiErrorMessage(profileQuery.error)}</p> : null}

      {profileQuery.data ? (
        <>
          <p>
            Username: <strong>{profileQuery.data.user.username}</strong>
          </p>
          <p>
            Email: <strong>{profileQuery.data.user.email}</strong>
          </p>

          <div className="form-grid">
            <label>
              Phone
              <input
                className="field"
                value={draft.phone ?? profileQuery.data.phone ?? ""}
                onChange={(event) => setDraft((prev) => ({ ...prev, phone: event.target.value }))}
              />
            </label>

            <label>
              Address
              <input
                className="field"
                value={draft.address ?? profileQuery.data.address ?? ""}
                onChange={(event) => setDraft((prev) => ({ ...prev, address: event.target.value }))}
              />
            </label>

            <label>
              City
              <input
                className="field"
                value={draft.city ?? profileQuery.data.city ?? ""}
                onChange={(event) => setDraft((prev) => ({ ...prev, city: event.target.value }))}
              />
            </label>

            <label>
              Country
              <input
                className="field"
                value={draft.country ?? profileQuery.data.country ?? ""}
                onChange={(event) => setDraft((prev) => ({ ...prev, country: event.target.value }))}
              />
            </label>
          </div>

          <div className="row-actions">
            <button
              className="primary-button"
              onClick={() => updateMutation.mutate()}
              disabled={updateMutation.isPending}
            >
              Save Profile
            </button>
          </div>
        </>
      ) : null}

      {updateMutation.isError ? <p className="error-text">{getApiErrorMessage(updateMutation.error)}</p> : null}
      {updateMutation.isSuccess ? <p className="success-text">Profile updated.</p> : null}
    </section>
  )
}