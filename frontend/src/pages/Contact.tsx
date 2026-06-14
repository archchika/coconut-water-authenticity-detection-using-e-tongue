import { useState, FormEvent } from "react";

/**
 * Contact page — address, phone, email + contact form (inspired by chl.lk).
 */
export default function Contact() {
  const [submitted, setSubmitted] = useState(false);
  const [formData, setFormData] = useState({ fullName: "", phone: "", email: "", message: "" });

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSubmitted(true);
    setFormData({ fullName: "", phone: "", email: "", message: "" });
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  return (
    <div className="public-contact-page">
      <section className="public-contact-two-col">
        <div className="public-contact-form-column">
          <h2 className="public-contact-form-title">Contact Form</h2>
          {submitted ? (
            <p className="public-contact-form-success">Thank you. Your message has been sent.</p>
          ) : (
            <form className="public-contact-form" onSubmit={handleSubmit}>
              <input
                type="text"
                name="fullName"
                placeholder="Full Name"
                value={formData.fullName}
                onChange={handleChange}
                className="public-contact-form-input"
                required
              />
              <input
                type="tel"
                name="phone"
                placeholder="Phone"
                value={formData.phone}
                onChange={handleChange}
                className="public-contact-form-input"
              />
              <input
                type="email"
                name="email"
                placeholder="Email Address"
                value={formData.email}
                onChange={handleChange}
                className="public-contact-form-input"
                required
              />
              <textarea
                name="message"
                placeholder="Message"
                value={formData.message}
                onChange={handleChange}
                className="public-contact-form-textarea"
                rows={5}
                required
              />
              <button type="submit" className="public-contact-form-submit">
                SUBMIT MESSAGE
              </button>
            </form>
          )}
        </div>

        <div className="public-contact-info-column">
          <h2 className="public-contact-info-title">Contact Info</h2>
          <div className="public-contact-info-block">
            <h3 className="public-contact-info-subhead">Locations</h3>
            <p><strong>Office:</strong> Ceylon Coco (Pvt) Ltd, 12 ABC Drive, Colombo 3, Sri Lanka</p>
            <p><strong>Factory:</strong> ABC drive, Dankotuwa, Sri Lanka</p>
          </div>
          <div className="public-contact-info-block">
            <h3 className="public-contact-info-subhead">Phone</h3>
            <p><a href="tel:+947712345678">+947712345678</a></p>
          </div>
          <div className="public-contact-info-block">
            <h3 className="public-contact-info-subhead">Email</h3>
            <p><a href="mailto:transparency@ceyloncoco.lk">transparency@ceyloncoco.lk</a></p>
          </div>
          <div className="public-contact-social">
            <a href="https://facebook.com" target="_blank" rel="noopener noreferrer" className="public-contact-social-icon" aria-label="Facebook">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" aria-hidden><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
            </a>
            <a href="https://twitter.com" target="_blank" rel="noopener noreferrer" className="public-contact-social-icon" aria-label="Twitter">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" aria-hidden><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
            </a>
          </div>
        </div>
        <div className="public-contact-template">
          <img src="/coconut-water-glass.png" alt="Coconut water — Ceylon Coco" className="public-contact-template-img" />
        </div>
      </section>

      <section className="public-section public-section-alt">
        <h2>More Inquiries</h2>
        <p>
          For product authenticity reports, calibration inquiries, or partnership, please use the contact details above or the form.
        </p>
      </section>
    </div>
  );
}
