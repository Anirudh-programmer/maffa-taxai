'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth, useUser } from '@clerk/nextjs'
import { Sidebar } from '@/components/layout/Sidebar'
import { useAuthStore } from '@/store'
import { authApi, setAuthToken, getAuthToken } from '@/lib/api'

// Persist sync state across client-side page unmounts/remounts
let globalSyncingInProgress = false

export function AppShell({ children }: { children: React.ReactNode }) {
  const { isSignedIn, isLoaded: isAuthLoaded, getToken } = useAuth()
  const { isLoaded: isUserLoaded, user: clerkUser } = useUser()
  const isLoaded = isAuthLoaded && isUserLoaded
  const router = useRouter()
  const { setUser, setToken, user } = useAuthStore()
  
  // React state to track synced status and force a re-render
  // Check synchronously on mount to prevent any single-frame flashing during tab switches
  const [syncedState, setSyncedState] = useState(() => {
    if (typeof window !== 'undefined') {
      const existingToken = getAuthToken()
      const currentUser = useAuthStore.getState().user
      if (existingToken && currentUser) {
        return true
      }
    }
    return false
  })

  useEffect(() => {
    if (!isLoaded) return
    if (!isSignedIn) {
      setSyncedState(false)
      router.push('/auth/sign-in')
      return
    }

    // Skip sync if already have a valid token and user profile in store
    const existingToken = getAuthToken()
    if (existingToken && user) {
      setSyncedState(true)
      return
    }

    if (syncedState || globalSyncingInProgress) {
      return
    }

    const syncAuth = async () => {
      globalSyncingInProgress = true
      try {
        const clerkToken = await getToken()
        if (!clerkToken) return
        
        // Pass email and name from Clerk to backend
        const email = clerkUser?.primaryEmailAddress?.emailAddress || undefined
        const fullName = clerkUser?.fullName || undefined
        
        const response = await authApi.syncClerk(clerkToken, email, fullName)
        setAuthToken(response.access_token)
        setToken(response.access_token)
        setUser(response.user)
        setSyncedState(true)
      } catch (err) {
        console.error('Auth sync failed:', err)
      } finally {
        globalSyncingInProgress = false
      }
    }
    syncAuth()
  }, [isSignedIn, isLoaded, user, clerkUser, syncedState])


  // Block rendering dashboard/children until Clerk is loaded and sync is complete
  if (!isLoaded || (isSignedIn && !syncedState)) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background">
        <div className="w-8 h-8 border-2 border-brand-500/30 border-t-brand-500 rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto relative">
        <div className="fixed inset-0 bg-mesh-gradient opacity-30 pointer-events-none z-0" />
        <div className="relative z-10 min-h-full">
          {children}
        </div>
      </main>
    </div>
  )
}
