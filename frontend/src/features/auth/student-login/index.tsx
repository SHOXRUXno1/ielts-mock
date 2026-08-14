import { z } from 'zod'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useNavigate } from '@tanstack/react-router'
import { useMutation } from '@tanstack/react-query'
import { Loader2, LogIn } from 'lucide-react'
import { toast } from 'sonner'
import { useAuthStore } from '@/stores/auth-store'
import { login } from '@/lib/api/auth'
import { decodeJwt } from '@/lib/api/admin'
import { Logo } from '@/assets/logo'
import { Button } from '@/components/ui/button'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { PasswordInput } from '@/components/password-input'

const formSchema = z.object({
  loginField: z.string().min(1, 'Please enter your login.'),
  password: z.string().min(1, 'Please enter your password.'),
})

export function StudentLogin() {
  const navigate = useNavigate()
  const { auth } = useAuthStore()

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: { loginField: '', password: '' },
  })

  const loginMutation = useMutation({
    mutationFn: (d: z.infer<typeof formSchema>) =>
      login({ login: d.loginField, password: d.password }),
    onSuccess: async (data) => {
      const token = data.access_token
      const payload = decodeJwt(token)
      auth.setAccessToken(token)
      const u = data.user
      auth.setUser({
        id: u.id,
        login: u.login,
        name: u.full_name || u.login,
        full_name: u.full_name,
        role: u.role,
        exp: payload.exp,
      })
      toast.success(`Welcome, ${u.full_name || u.login}!`)
      if (u.role === 'admin') {
        void navigate({ to: '/', replace: true })
      } else {
        void navigate({ to: '/student/dashboard', replace: true })
      }
    },
    onError: () => {
      toast.error('Invalid login or password.')
    },
  })

  const isLoading = loginMutation.isPending

  return (
    <div className='flex min-h-svh items-center justify-center bg-muted/40 p-4'>
      <div className='w-full max-w-md rounded-2xl bg-background p-10 shadow-xl'>
        <div className='mb-8 flex flex-col items-center gap-3 text-center'>
          <Logo className='h-10 w-10' />
          <h1 className='text-3xl font-bold tracking-tight'>IELTS Mock</h1>
          <p className='text-muted-foreground text-sm'>
            Sign in to continue
          </p>
        </div>

        <Form {...form}>
          <form onSubmit={form.handleSubmit((d) => loginMutation.mutate(d))} className='space-y-5'>
            <FormField
              control={form.control}
              name='loginField'
              render={({ field }) => (
                <FormItem>
                  <FormLabel className='text-sm font-medium'>Login</FormLabel>
                  <FormControl>
                    <Input
                      className='h-11 rounded-lg px-4 text-sm'
                      placeholder='••••••••'
                      autoComplete='username'
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name='password'
              render={({ field }) => (
                <FormItem>
                  <FormLabel className='text-sm font-medium'>Password</FormLabel>
                  <FormControl>
                    <PasswordInput
                      className='h-11 rounded-lg px-4 text-sm'
                      placeholder='••••••••'
                      autoComplete='current-password'
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Button className='mt-2 h-11 w-full rounded-lg text-sm font-semibold' disabled={isLoading}>
              {isLoading ? <Loader2 className='mr-2 h-4 w-4 animate-spin' /> : <LogIn className='mr-2 h-4 w-4' />}
              Sign in
            </Button>
          </form>
        </Form>

      </div>
    </div>
  )
}
