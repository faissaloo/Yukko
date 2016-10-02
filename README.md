Yukko
===
Yukko is an ASCIIpunk NNTPchan client written in Python 3. Place a list 
of nodes seperated by new lines in nodeList.txt and the client will cycle 
through them at random. nntp.py is the library I have written for this 
project, it has been intentionally written in such a way that it does not 
depend on anything in the rest of the program, this allows it 
to be pulled out and used for other projects.  
  
Screenies  
==  
![Board overview](https://i.sli.mg/1z0JdC.png)  
![CAPTCHA](https://i.sli.mg/qEzWgR.png)
![Post](https://i.sli.mg/fxw7hX.png)
![Board list](https://i.sli.mg/LUS71H.png)  
![Attachments](https://i.sli.mg/FOzIo1.png)  
  
Controls
==  

Board overview  
=  
 - Left/Right: Change page  
 - Up/Down: Scroll  
 - Enter: Open thread  
 - Escape: Go to board  
 - P: New thread  
 - B: Board list  
 - R: Refresh  

Thread
=  
 - Backspace/Left/Escape: Back to board overview.  
 - Up/Down: Scroll
 - Enter: View attachments (does nothing if there are none)  
 - P: New reply  
 - R: Refresh    
  
Attachments  
=  
 - Up/Down: Scroll
 - Enter: Download attachment
 - Backspace/Left/Escape: Back to thread  
  
Settings  
==  
General settings are stored in settings.json  
  
download directory  
=  
The directory to download attachments to.  
  
text editor
=  
The command used to open a text editor.  

theme folder  
=  
The directory holding the current theme.  

max overview lines  
=  
The maximum amount of lines to show in board overview mode before contracting the post.

max overview posts  
=  
The maxmimum amount of posts, starting from the end of the thread (not including the opening post) to show in board view mode.
  
default board  
=  
The default board that Yukko will go to when started.  

http proxy/https proxy  
=  
Sets a proxy for all traffic, such as "socks5://127.0.0.1:9050". Note that SOCKS proxies will require the socks add-on for the requests module, which can be 
installed like so:  
```
sudo pip install -U "requests[socks]"
```  
  
Themes
==
Themes can be used to style Yukko to look however you like, from changing the ascii art to the borders around the posts.  
They contain 5 files:  
 - attachmentsBg.txt: The background to display on the attachments page.  
 - boardListBg.txt: The background to display on the board list page.  
 - emptyBoard.txt: The background to display in the case that a board is empty.  
 - errorRetrievingPage.txt: The background to display in the case that an error occurs while attempting to obtain the board.  
 - posts.json: Contains information for the styling of posts  
  - global: Applies to both opening posts and normal posts  
  - local: Applies to either opening posts or normal posts  
   - default: Style data for a normal post  
   - OP: Style data for an opening post  
    - unselected: Style data for when a post is not selected
    - selected: Style data for when a post is selected  
     - seperator: The seperating line between each post
     - seperator repeat: The character that will be repeated in the case that the terminal is wider than the seperator
     - header: The header for each post, supporting python's formatting mini language. Spaces are occupied like so:
      1. Name
      2. Subject
      3. Post ID
      4. Date
      5. Attachment character
     - body: The string to repeat vertically along the body of the post
     - footer: The string to use for the end of a post
     - footer repeat: The string to repeat horizontally along the body of the post in the case that the width of the terminal is larger than that of the footer.
