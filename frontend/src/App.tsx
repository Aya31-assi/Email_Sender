import { FormEvent, useEffect, useState } from 'react';
import { ArrowUpRight, Check, Languages, Send, ShieldCheck, Sparkles } from 'lucide-react';
import { api } from './services/api';

type EmailLanguage = 'ar' | 'en';

type FormData = {
  recipient_email: string;
  recipient_name: string;
  business_name: string;
  platform_username: string;
  platform_password: string;
  subject: string;
  language: EmailLanguage;
  recipient_agreed: boolean;
};

type FormField = {
  key: Exclude<keyof FormData, 'recipient_agreed' | 'language'>;
  label: string;
  type?: string;
  placeholder?: string;
  maxLength?: number;
  autoComplete?: string;
  full?: boolean;
};

const initialForm: FormData = {
  recipient_email: '',
  recipient_name: '',
  business_name: '',
  platform_username: '',
  platform_password: '',
  subject: 'Welcome to Qredit - Your account is ready',
  language: 'en',
  recipient_agreed: false,
};

const languageOptions: Array<{ value: EmailLanguage; label: string; hint: string; subject: string }> = [
  {
    value: 'en',
    label: 'English',
    hint: 'Send the English welcome design',
    subject: 'Welcome to Qredit - Your account is ready',
  },
  {
    value: 'ar',
    label: 'العربية',
    hint: 'إرسال قالب الترحيب العربي',
    subject: 'أهلاً بك في Qredit - حسابك جاهز',
  },
];

const fields: FormField[] = [
  { key: 'recipient_email', label: 'Recipient email', type: 'email', placeholder: 'hello@business.com', maxLength: 254 },
  { key: 'recipient_name', label: 'Recipient name', placeholder: 'Alex Morgan', maxLength: 120 },
  { key: 'business_name', label: 'Business name', placeholder: 'Acme & Co.', maxLength: 160, full: true },
  { key: 'platform_username', label: 'Platform username', placeholder: 'customer.username', maxLength: 160, autoComplete: 'off' },
  { key: 'platform_password', label: 'Platform password', placeholder: 'Temporary password', maxLength: 160, autoComplete: 'new-password' },
  { key: 'subject', label: 'Subject', maxLength: 200, full: true },
];

function getErrorMessage(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback;
}

function Login({ onLogin }: { onLogin: (email: string, password: string) => Promise<void> }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError('');
    setLoading(true);
    try {
      await onLogin(email, password);
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to sign in.'));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-shell">
      <section className="login-panel">
        <div className="brand-mark">
          <Sparkles size={18} />
        </div>
        <p className="kicker">QREDIT / ADMIN</p>
        <h1>Send Qredit emails with care.</h1>
        <p className="lede">A focused workspace for welcome messages and onboarding access.</p>

        <form onSubmit={submit} className="stack">
          <label>
            Email address
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
              autoComplete="username"
              placeholder="you@company.com"
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
              autoComplete="current-password"
              placeholder="Your password"
            />
          </label>
          {error && <div className="alert error">{error}</div>}
          <button className="button primary" disabled={loading}>
            {loading ? 'Checking access...' : 'Enter workspace'}
            <ArrowUpRight size={17} />
          </button>
        </form>

        <div className="secure-note">
          <ShieldCheck size={17} />
          Private admin access
        </div>
      </section>

      <aside className="login-aside">
        <span>01</span>
        <p>
          Welcome emails
          <br />
          that feel ready.
        </p>
      </aside>
    </main>
  );
}

function Composer({ email }: { email: string }) {
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [loading, setLoading] = useState(false);

  function update(key: keyof FormData, value: string | boolean) {
    setForm((current) => {
      const next = { ...current, [key]: value };
      // Keep the default subject aligned with the message language. The admin
      // can still type a custom subject afterwards.
      if (key === 'language') {
        next.subject = languageOptions.find((option) => option.value === value)?.subject ?? next.subject;
      }
      return next;
    });
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError('');
    setNotice('');

    if (!form.recipient_agreed) {
      setError('Please confirm the recipient agreed to receive this email.');
      return;
    }

    setLoading(true);
    try {
      const result = await api.sendEmail(form);
      setNotice(result.message);
      setForm(initialForm);
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to send email.'));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="top-brand">
          <div className="brand-mark small">
            <Sparkles size={15} />
          </div>
          <span>QREDIT</span>
          <i>/</i>
          <strong>OUTREACH</strong>
        </div>
        <span className="user-email">{email}</span>
      </header>

      <div className="workspace composer-workspace">
        <div className="intro simple-intro">
          <h1>Send Qredit Email</h1>
          <div className="shield">
            <ShieldCheck size={19} />
            <span>
              Local workspace
              <br />
              <small>Development mode</small>
            </span>
          </div>
        </div>

        <form className="form-panel" onSubmit={submit}>
          <div className="section-title">
            <span>01</span>
            <div>
              <h2>Message details</h2>
              <p>Tell us who you're writing to.</p>
            </div>
          </div>

          <div className="fields">
            <div className="language-group full" role="radiogroup" aria-label="Email language">
              <div className="language-heading">
                <Languages size={17} />
                <span>Email language</span>
              </div>
              <div className="language-toggle">
                {languageOptions.map((option) => (
                  <button
                    type="button"
                    key={option.value}
                    className={form.language === option.value ? 'language-option active' : 'language-option'}
                    onClick={() => update('language', option.value)}
                    role="radio"
                    aria-checked={form.language === option.value}
                  >
                    <strong>{option.label}</strong>
                    <small>{option.hint}</small>
                  </button>
                ))}
              </div>
            </div>
            {fields.map((field) => (
              <label key={field.key} className={field.full ? 'full' : undefined}>
                {field.label}
                <input
                  type={field.type ?? 'text'}
                  value={form[field.key]}
                  onChange={(event) => update(field.key, event.target.value)}
                  required
                  maxLength={field.maxLength}
                  placeholder={field.placeholder}
                  autoComplete={field.autoComplete}
                />
              </label>
            ))}
          </div>

          <label className="consent">
            <input
              type="checkbox"
              checked={form.recipient_agreed}
              onChange={(event) => update('recipient_agreed', event.target.checked)}
            />
            <span>
              <Check size={14} />
              I confirm this recipient has agreed to receive this email.
            </span>
          </label>

          {error && <div className="alert error">{error}</div>}
          {notice && <div className="alert success">{notice}</div>}

          <button className="button primary send-button" disabled={loading}>
            {loading ? 'Sending securely...' : 'Send email'}
            {loading ? <span className="spinner" /> : <Send size={17} />}
          </button>
        </form>
      </div>
    </main>
  );
}

export default function App() {
  const [email, setEmail] = useState<string | null>(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    api
      .me()
      .then((user) => setEmail(user.email))
      .catch(() => setEmail(null))
      .finally(() => setChecking(false));
  }, []);

  async function login(emailAddress: string, password: string) {
    const user = await api.login(emailAddress, password);
    setEmail(user.email);
  }

  if (checking) {
    return <div className="loading-screen">Loading workspace...</div>;
  }

  return email ? <Composer email={email} /> : <Login onLogin={login} />;
}
