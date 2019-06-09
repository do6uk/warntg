# warntg (switch talkgroups on brandmeister.network on dwd-warning)
Steuerung von Talkgroups auf dem Repeater/Hotspot im Brandmeister-Netzwerk in Abhängigkeit von DWD-Warnungen

# Was macht es?
Dieses Skript schaltet auf unserem Repeater DB0USD bei einer bestehenden Unwetterwarnung die häufig frequentierten TGs 262 und 263 auf dem Timeslot 1 ab (also auf dynamisch), damit die dort auch gebuchte TG 263113 (Unwetter-TG) durchgängig gehört werden kann.
Am Ende der Warnlage werden die TGs 262 und 263 wieder auf dem Timeslot 1 gebucht (also auf statisch) und der Repeater arbeitet wieder wie gewohnt.
Die Umschaltung wird parallel über einen BOT (WebALARM-BOT) in den Telegram-Messenger eingespielt, so dass die Admins und ggf. User die Änderung auch mitbekommen.

# Wie funktioniert das?
Das Skript ruft die Warndaten über das JSONP-File vom DWD ab und prüft auf die im Skript einstellbaren WarnCellIds, die WarnTypes und die WarnLevels.
Zu jedem WarnType kann ein Mindestlevel oder eine Liste von überwachten Leveln eingestellt werden, so dass beispielsweise die Umschaltung bei Gewitter schon ab Stufe 2 und bei Wind nur bei Stufe 4 erfolgen kann.
Wird mindestens eine Warnung erkannt, werden die zuvor definierten TGs auf den jeweiligen Repeatern oder Hotspots (mehrere sind hier möglich) aus dem statischen Mapping entfernt. Dazu wird die selbe BM-API wie beim PiStar genutzt.
Die aktive Warnlage wird in der Datei  warntg.state  gespeichert, so dass beim nächsten Aufruf und immernoch bestehender Warnlage keine Änderung der TGs erfolgt.
Ist die Warnlage bei einem weiteren Skriptdurchlauf beendet, werden die TGs im Brandmeister wieder statisch gebucht und der neue Status in der  warntg.state  gespeichert.

# Was kann man noch machen?
Durch einen Aufruf des Skriptes mit 0 oder 1 als erstem Argument kann man eine Normallage oder Warnlage simulieren und die Schaltung der TGs entsprechend testen.

# Was geht (noch) nicht?
- Derzeit kann man nur festlegen, welche TGs "abgeschaltet" werden sollen. Denkbar wären zukünftig noch andere Szenarien, bei denen mal TGs "einschaltet" oder auf einen anderen Timeslot "verschiebt". 
- Eine Benachrichtigung per DAPNET ist derzeit auch noch nicht möglich, aber für die Zukunft geplant. Großer Vorteil wäre hier, dass die Info bei entsprechender Verknüpfung auch auf dem eingeschalteten Funkgerät erscheint.

# Es funktioniert nicht?
Das ist sehr schade, aber dann schreib mir einfach an  do6uk [auf] ralsu.de  und vielleicht können wir das Problem zusammen lösen.
