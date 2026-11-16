from django.conf import settings
from django.db import models
from django.utils.text import slugify
import markdown
import nh3


class PostStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    PENDING = 'PENDING', 'Pending Review'
    APPROVED = 'APPROVED', 'Approved'
    REJECTED = 'REJECTED', 'Rejected'


class Post(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    body = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    status = models.CharField(
        max_length=20,
        choices=PostStatus.choices,
        default=PostStatus.DRAFT,
        db_index=True
    )
    rejection_reason = models.TextField(blank=True, default='')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_posts'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    is_edited_after_approval = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or 'post'
            slug = base_slug
            counter = 1
            while Post.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def rendered_body(self):
        """Render markdown to HTML safely using nh3 to prevent XSS."""
        html = markdown.markdown(
            self.body,
            extensions=['extra', 'codehilite', 'nl2br']
        )
        allowed_tags = {
            'a', 'b', 'blockquote', 'code', 'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'hr', 'i', 'li', 'ol', 'p', 'pre', 'strong', 'ul', 'br'
        }
        allowed_attributes = {'a': {'href', 'title'}}
        return nh3.clean(html, tags=allowed_tags, attributes=allowed_attributes)
