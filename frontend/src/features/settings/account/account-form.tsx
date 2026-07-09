import { z } from 'zod'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import { changePassword, changeName } from '@/lib/api/admin'
import { useAuthStore } from '@/stores/auth-store'
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
import { Separator } from '@/components/ui/separator'

// ---------------------------------------------------------------------------
// Change Display Name
// ---------------------------------------------------------------------------

const nameSchema = z.object({
  new_name: z.string().min(1, 'Name cannot be empty.'),
})

function ChangeNameForm() {
  const { auth } = useAuthStore()
  const currentName = auth.user?.name ?? ''

  const form = useForm<z.infer<typeof nameSchema>>({
    resolver: zodResolver(nameSchema),
    defaultValues: { new_name: currentName },
  })

  const mutation = useMutation({
    mutationFn: (values: z.infer<typeof nameSchema>) => changeName({ new_name: values.new_name }),
    onSuccess: (data) => {
      const user = auth.user
      if (user) auth.setUser({ ...user, name: data.new_name })
      toast.success('Display name updated.')
    },
    onError: () => toast.error('Failed to update name.'),
  })

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit((d) => mutation.mutate(d))} className='space-y-4'>
        <FormField
          control={form.control}
          name='new_name'
          render={({ field }) => (
            <FormItem>
              <FormLabel>Display Name</FormLabel>
              <FormControl>
                <Input placeholder='Your name' {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button type='submit' disabled={mutation.isPending}>
          {mutation.isPending ? 'Saving…' : 'Update Name'}
        </Button>
      </form>
    </Form>
  )
}

// ---------------------------------------------------------------------------
// Change Password
// ---------------------------------------------------------------------------

const passwordSchema = z
  .object({
    current_password: z.string().min(1, 'Please enter your current password.'),
    new_password: z.string().min(4, 'New password must be at least 4 characters.'),
    confirm_password: z.string().min(1, 'Please confirm your new password.'),
  })
  .refine((d) => d.new_password === d.confirm_password, {
    message: "Passwords don't match.",
    path: ['confirm_password'],
  })

function ChangePasswordForm() {
  const form = useForm<z.infer<typeof passwordSchema>>({
    resolver: zodResolver(passwordSchema),
    defaultValues: { current_password: '', new_password: '', confirm_password: '' },
  })

  const mutation = useMutation({
    mutationFn: (values: z.infer<typeof passwordSchema>) =>
      changePassword({ current_password: values.current_password, new_password: values.new_password }),
    onSuccess: () => {
      toast.success('Password changed successfully.')
      form.reset()
    },
    onError: () => toast.error('Current password is incorrect.'),
  })

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit((d) => mutation.mutate(d))} className='space-y-4'>
        <FormField
          control={form.control}
          name='current_password'
          render={({ field }) => (
            <FormItem>
              <FormLabel>Current Password</FormLabel>
              <FormControl><PasswordInput placeholder='••••••••' {...field} /></FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name='new_password'
          render={({ field }) => (
            <FormItem>
              <FormLabel>New Password</FormLabel>
              <FormControl><PasswordInput placeholder='••••••••' {...field} /></FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name='confirm_password'
          render={({ field }) => (
            <FormItem>
              <FormLabel>Confirm New Password</FormLabel>
              <FormControl><PasswordInput placeholder='••••••••' {...field} /></FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button type='submit' disabled={mutation.isPending}>
          {mutation.isPending ? 'Saving…' : 'Change Password'}
        </Button>
      </form>
    </Form>
  )
}

// ---------------------------------------------------------------------------
// Combined AccountForm
// ---------------------------------------------------------------------------

export function AccountForm() {
  const { auth } = useAuthStore()
  const login = auth.user?.login ?? ''

  return (
    <div className='space-y-8'>
      {/* Login — readonly info */}
      <div>
        <p className='text-sm font-medium mb-1.5'>Login</p>
        <Input value={login} readOnly className='bg-muted text-muted-foreground max-w-sm' />
      </div>

      <ChangeNameForm />

      <Separator />

      <div>
        <h3 className='mb-4 text-sm font-medium'>Change Password</h3>
        <ChangePasswordForm />
      </div>
    </div>
  )
}
