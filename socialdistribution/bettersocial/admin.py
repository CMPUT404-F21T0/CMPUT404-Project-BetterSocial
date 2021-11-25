from django.contrib import admin

from .models import Author, Post, Comment, Like, LikedRemote, Follower, Following, InboxItem, Node, UUIDRemoteCache

admin.site.register(Author)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Like)

admin.site.register(LikedRemote)

admin.site.register(Follower)
admin.site.register(Following)

admin.site.register(InboxItem)

admin.site.register(Node)

admin.site.register(UUIDRemoteCache)
