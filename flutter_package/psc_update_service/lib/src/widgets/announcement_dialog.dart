import 'package:flutter/material.dart';

import '../models/announcement.dart';

/// Shows an in-app announcement dialog (not a system notification).
Future<void> showPscAnnouncementDialog(
  BuildContext context, {
  required PscAnnouncement announcement,
}) async {
  await showDialog<void>(
    context: context,
    barrierDismissible: true,
    builder: (context) => AlertDialog(
      title: Text(announcement.title),
      content: SingleChildScrollView(
        child: Text(announcement.message),
      ),
      actions: [
        FilledButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Got it'),
        ),
      ],
    ),
  );
}
